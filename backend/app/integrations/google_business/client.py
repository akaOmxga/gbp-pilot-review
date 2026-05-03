from collections.abc import Sequence
from typing import Any

import httpx

from app.config import get_settings
from app.integrations.google_business.exceptions import (
    GoogleApi5xxError,
    GoogleAuthError,
    GoogleNetworkError,
    GoogleRateLimitError,
)
from app.integrations.google_business.schemas import (
    GoogleLocation,
    GoogleReview,
    GoogleReviewReplyResult,
    GoogleTokenResponse,
)

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
ACCOUNT_MGMT_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
BUSINESS_INFO_BASE = "https://mybusinessbusinessinformation.googleapis.com/v1"
LEGACY_REVIEWS_BASE = "https://mybusiness.googleapis.com/v4"


def _check_status(response: httpx.Response) -> None:
    if 200 <= response.status_code < 300:
        return
    if response.status_code == 401 or response.status_code == 403:
        raise GoogleAuthError(f"{response.status_code}: {response.text[:200]}")
    if response.status_code == 429:
        retry_after = response.headers.get("retry-after")
        raise GoogleRateLimitError(retry_after=int(retry_after) if retry_after else None)
    if response.status_code >= 500:
        raise GoogleApi5xxError(f"{response.status_code}: {response.text[:200]}")
    response.raise_for_status()


class GoogleBusinessClient:
    """Real Google Business Profile API client (httpx)."""

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(timeout=30.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def exchange_code(self, code: str, redirect_uri: str) -> GoogleTokenResponse:
        settings = get_settings()
        try:
            response = await self._http.post(
                OAUTH_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_oauth_client_id.get_secret_value(),
                    "client_secret": settings.google_oauth_client_secret.get_secret_value(),
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(response)
        return GoogleTokenResponse.model_validate(response.json())

    async def refresh_token(self, refresh_token: str) -> GoogleTokenResponse:
        settings = get_settings()
        try:
            response = await self._http.post(
                OAUTH_TOKEN_URL,
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.google_oauth_client_id.get_secret_value(),
                    "client_secret": settings.google_oauth_client_secret.get_secret_value(),
                    "grant_type": "refresh_token",
                },
            )
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(response)
        payload = response.json()
        # Google does not always re-emit a refresh_token on refresh — keep the old one.
        if "refresh_token" not in payload:
            payload["refresh_token"] = refresh_token
        return GoogleTokenResponse.model_validate(payload)

    async def revoke_token(self, token: str) -> None:
        try:
            await self._http.post(OAUTH_REVOKE_URL, params={"token": token})
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc

    async def list_locations(self, access_token: str) -> Sequence[GoogleLocation]:
        headers = {"Authorization": f"Bearer {access_token}"}
        accounts_url = f"{ACCOUNT_MGMT_BASE}/accounts"
        try:
            accounts_resp = await self._http.get(accounts_url, headers=headers)
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(accounts_resp)
        accounts = accounts_resp.json().get("accounts", [])
        locations: list[GoogleLocation] = []
        for account in accounts:
            account_name = account["name"]  # e.g. "accounts/123"
            params = {"readMask": "name,title,categories.primaryCategory.name,storefrontAddress"}
            try:
                loc_resp = await self._http.get(
                    f"{BUSINESS_INFO_BASE}/{account_name}/locations",
                    headers=headers,
                    params=params,
                )
            except httpx.HTTPError as exc:
                raise GoogleNetworkError(str(exc)) from exc
            _check_status(loc_resp)
            for raw in loc_resp.json().get("locations", []):
                locations.append(
                    GoogleLocation(
                        name=f"{account_name}/{raw['name']}",
                        title=raw.get("title", "(unnamed)"),
                        primary_category=(
                            raw.get("categories", {}).get("primaryCategory", {}).get("name")
                        ),
                        address_lines=raw.get("storefrontAddress", {}).get("addressLines", []),
                    )
                )
        return locations

    async def list_reviews(
        self, access_token: str, location_name: str, page_token: str | None = None
    ) -> tuple[Sequence[GoogleReview], str | None]:
        url = f"{LEGACY_REVIEWS_BASE}/{location_name}/reviews"
        params: dict[str, Any] = {"pageSize": 50}
        if page_token:
            params["pageToken"] = page_token
        try:
            response = await self._http.get(
                url, headers={"Authorization": f"Bearer {access_token}"}, params=params
            )
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(response)
        body = response.json()
        reviews: list[GoogleReview] = []
        for raw in body.get("reviews", []):
            reviews.append(
                GoogleReview(
                    name=raw["name"],
                    review_id=raw["reviewId"],
                    reviewer_display_name=raw.get("reviewer", {}).get("displayName"),
                    rating=_star_to_int(raw.get("starRating", "FIVE")),
                    comment=raw.get("comment"),
                    create_time=raw["createTime"],
                    update_time=raw.get("updateTime"),
                )
            )
        return reviews, body.get("nextPageToken")

    async def reply_to_review(
        self, access_token: str, review_name: str, comment: str
    ) -> GoogleReviewReplyResult:
        url = f"{LEGACY_REVIEWS_BASE}/{review_name}/reply"
        try:
            response = await self._http.put(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                json={"comment": comment},
            )
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(response)
        return GoogleReviewReplyResult.model_validate(response.json())

    async def delete_reply(self, access_token: str, review_name: str) -> None:
        url = f"{LEGACY_REVIEWS_BASE}/{review_name}/reply"
        try:
            response = await self._http.delete(
                url, headers={"Authorization": f"Bearer {access_token}"}
            )
        except httpx.HTTPError as exc:
            raise GoogleNetworkError(str(exc)) from exc
        _check_status(response)


_STAR_MAP = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}


def _star_to_int(star: str) -> int:
    return _STAR_MAP.get(star, 5)
