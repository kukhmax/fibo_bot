import json
from urllib import parse
from urllib import request

from core.bot.runtime import IncomingMessage


class TelegramApiTransport:
    def __init__(
        self,
        bot_token: str,
        base_url: str = "https://api.telegram.org",
        poll_timeout_seconds: int = 20,
    ) -> None:
        cleaned_token = bot_token.strip()
        if not cleaned_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        self._bot_token = cleaned_token
        self._base_url = base_url.rstrip("/")
        self._poll_timeout_seconds = poll_timeout_seconds

    def fetch_updates(self, offset: int | None = None, limit: int = 50) -> list[IncomingMessage]:
        params = {
            "limit": str(limit),
            "timeout": str(self._poll_timeout_seconds),
        }
        if offset is not None:
            params["offset"] = str(offset)
        query = parse.urlencode(params)
        url = f"{self._api_url('/getUpdates')}?{query}"
        req = request.Request(url, method="GET")
        payload = _fetch_json(req)
        results = payload.get("result", [])
        if not isinstance(results, list):
            return []
        updates: list[IncomingMessage] = []
        for item in results:
            parsed = _parse_incoming_message(item)
            if parsed is not None:
                updates.append(parsed)
        updates.sort(key=lambda x: x.update_id)
        return updates

    def send_text(
        self,
        chat_id: int,
        text: str,
        reply_keyboard: tuple[tuple[str, ...], ...] | None = None,
    ) -> None:
        payload: dict[str, object] = {
            "chat_id": chat_id,
            "text": text,
        }
        if reply_keyboard is not None:
            payload["reply_markup"] = {
                "keyboard": [[{"text": value} for value in row] for row in reply_keyboard],
                "resize_keyboard": True,
                "is_persistent": True,
            }
        req = request.Request(
            self._api_url("/sendMessage"),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        _fetch_json(req)

    def _api_url(self, method: str) -> str:
        return f"{self._base_url}/bot{self._bot_token}{method}"


def _parse_incoming_message(payload: object) -> IncomingMessage | None:
    if not isinstance(payload, dict):
        return None
    if "update_id" not in payload or not isinstance(payload["update_id"], int):
        return None
    message = payload.get("message")
    if not isinstance(message, dict):
        return None
    text = message.get("text")
    if not isinstance(text, str) or not text.strip():
        return None
    chat = message.get("chat")
    from_user = message.get("from")
    if not isinstance(chat, dict) or not isinstance(from_user, dict):
        return None
    chat_id = chat.get("id")
    user_id = from_user.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        return None
    return IncomingMessage(
        update_id=int(payload["update_id"]),
        chat_id=chat_id,
        user_id=user_id,
        text=text.strip(),
    )


def _fetch_json(req: request.Request) -> dict[str, object]:
    with request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise RuntimeError("Telegram API returned non-object response")
    if not parsed.get("ok", True):
        description = parsed.get("description", "unknown error")
        raise RuntimeError(f"Telegram API error: {description}")
    return parsed
