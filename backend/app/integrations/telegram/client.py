import httpx

from app.config import get_settings


class TelegramError(Exception):
    pass


class TelegramClient:
    BASE_URL = "https://api.telegram.org"

    def __init__(self, http: httpx.AsyncClient | None = None) -> None:
        self._http = http or httpx.AsyncClient(timeout=15.0)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def send_message(self, *, chat_id: str, text: str) -> int:
        settings = get_settings()
        if settings.telegram_bot_token is None:
            raise TelegramError("Telegram bot token not configured")
        token = settings.telegram_bot_token.get_secret_value()
        try:
            response = await self._http.post(
                f"{self.BASE_URL}/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            )
        except httpx.HTTPError as exc:
            raise TelegramError(str(exc)) from exc
        if response.status_code >= 400:
            raise TelegramError(f"Telegram {response.status_code}: {response.text[:200]}")
        body = response.json()
        return int(body.get("result", {}).get("message_id", 0))
