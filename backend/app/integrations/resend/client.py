import httpx

from app.config import get_settings


class ResendError(Exception):
    pass


class ResendClient:
    BASE_URL = "https://api.resend.com"

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def send_email(
        self,
        *,
        to: str,
        subject: str,
        html: str,
        text: str | None = None,
    ) -> str:
        settings = get_settings()
        try:
            response = await self._http.post(
                f"{self.BASE_URL}/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key.get_secret_value()}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.resend_from_email,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                    "text": text or "",
                },
            )
        except httpx.HTTPError as exc:
            raise ResendError(str(exc)) from exc
        if response.status_code >= 400:
            raise ResendError(f"Resend {response.status_code}: {response.text[:200]}")
        return str(response.json().get("id", ""))
