# SECRETS.md — Правила загрузки секретов

## Источники значений

1. Переменные окружения процесса.
2. `.env` файл, если путь передан в `load_runtime_secrets`.
3. Значения по умолчанию для `APP_ENV` (`dev`) и `LOG_LEVEL` (`INFO`).

## Обязательные секреты

- `TELEGRAM_BOT_TOKEN` — обязателен всегда.

## Торговые секреты

- `HYPERLIQUID_API_KEY`
- `HYPERLIQUID_API_SECRET`
- `MEXC_API_KEY`
- `MEXC_API_SECRET`

Валидация торговых секретов включается флагом `require_trading_credentials=True`.

## Шаблон

- Использовать `.env.example` как базовый шаблон.
- Рабочий `.env` не коммитить в репозиторий.
