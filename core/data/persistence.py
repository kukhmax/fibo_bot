from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from core.data.models import Candle


class StateCache:
    def __init__(self, file_path: str | Path = "runtime/state_cache.json") -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {}
        raw = self.file_path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {}
        return parsed

    def save(self, state: dict[str, Any]) -> None:
        self.file_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        state = self.load()
        return state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        state = self.load()
        state[key] = value
        self.save(state)


class LocalCandleHistory:
    def __init__(self, base_dir: str | Path = "runtime/history") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append(self, candle: Candle) -> None:
        path = self._history_file(candle.symbol, candle.timeframe)
        payload = json.dumps(asdict(candle), ensure_ascii=False)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(payload + "\n")

    def load(self, symbol: str, timeframe: str, limit: int | None = None) -> list[Candle]:
        path = self._history_file(symbol, timeframe)
        if not path.exists():
            return []
        raw_lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if limit is not None:
            raw_lines = raw_lines[-max(0, limit) :]
        candles: list[Candle] = []
        for line in raw_lines:
            payload = json.loads(line)
            candles.append(
                Candle(
                    symbol=payload["symbol"],
                    timeframe=payload["timeframe"],
                    open_time_ms=int(payload["open_time_ms"]),
                    close_time_ms=int(payload["close_time_ms"]),
                    open=float(payload["open"]),
                    high=float(payload["high"]),
                    low=float(payload["low"]),
                    close=float(payload["close"]),
                    volume=float(payload["volume"]),
                )
            )
        return candles

    def _history_file(self, symbol: str, timeframe: str) -> Path:
        normalized_symbol = symbol.replace("/", "_")
        return self.base_dir / f"{normalized_symbol}_{timeframe}.jsonl"
