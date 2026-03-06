# Fibo Bot

Telegram-бот для сигналов, paper-торговли и подготовки к live-режиму с контролем риска, mini-backtest, ML-фильтром и новостным risk-gate.

## Возможности

- Режимы работы: `signal_only`, `paper`, `live`
- Управление настройками через Telegram-меню и команды
- Контроль риска:
  - риск на сделку
  - дневной лимит просадки (DD)
  - лимит открытых позиций
  - SL/TP и RR
- Mini-backtest по `BTCUSDT|ETHUSDT|SOLUSDT`
- Whitelist активов по ликвидности и спреду
- News risk filter (блокировка входов при риск-новостях)
- Health-check и запуск в Docker (app + redis + postgres)

## Архитектура проекта

```text
fib_bot/
├─ core/
│  ├─ bot/           # Telegram runtime, команды, меню, репортеры, risk/news gates
│  ├─ config/        # Загрузка профилей окружения и секретов
│  ├─ data/          # WS/REST, свечной pipeline, quality/persistence
│  ├─ strategies/    # Торговые стратегии + selector
│  ├─ regime/        # Классификатор рыночного режима
│  ├─ risk/          # RiskManager, DailyDrawdownGuard
│  ├─ ml/            # ML inference/training артефакты и пайплайны
│  └─ backtest/      # История и mini-backtest
├─ infra/docker/     # Dockerfile и docker-compose
├─ tests/            # Unit/integration тесты
├─ docs/             # Документация (включая секреты)
└─ DEVELOP.md        # Журнал этапов разработки
```

## Требования

- Python `3.11+`
- Docker Desktop + Docker Compose (для контейнерного запуска)
- Telegram Bot Token

## Быстрый старт (локально)

1. Скопируйте env-шаблон:

```powershell
Copy-Item .env.example .env
```

2. Заполните минимум:
   - `TELEGRAM_BOT_TOKEN`
   - при необходимости ключи бирж:
     - `HYPERLIQUID_API_KEY`
     - `HYPERLIQUID_API_SECRET`
     - `MEXC_API_KEY`
     - `MEXC_API_SECRET`

3. Запуск:

```powershell
python -m core.bot.main
```

4. Проверка health:

```powershell
python -m core.bot.main --health
```

5. Проверка доступных команд (без polling):

```powershell
python -m core.bot.main --commands --once
```

## Запуск в Docker

```powershell
docker compose -f infra/docker/docker-compose.yml up -d --build
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs --no-color --tail 100 app
```

## Полный reset Docker с очисткой кэша

```powershell
docker compose -f infra/docker/docker-compose.yml down --volumes --remove-orphans
docker builder prune -af
docker image prune -af
docker volume prune -f
docker network prune -f
docker compose -f infra/docker/docker-compose.yml build --no-cache
docker compose -f infra/docker/docker-compose.yml up -d
docker compose -f infra/docker/docker-compose.yml ps
docker compose -f infra/docker/docker-compose.yml logs --no-color --tail 120 app
```

## Конфигурация окружений

Используется переменная `APP_ENV`:

- `dev` — базовый рабочий профиль (`signal_only`, `full_access`)
- `paper` — профиль paper-режима (`paper`, `full_access`)
- `test` — профиль с `notify_only` (изменения настроек в чате ограничены)

Файлы профилей:

- `core/config/profiles/dev.json`
- `core/config/profiles/paper.json`
- `core/config/profiles/test.json`

## Ключевые env-переменные

### Базовые

- `APP_ENV` — профиль конфигурации (`dev|paper|test`)
- `LOG_LEVEL` — уровень логирования
- `TELEGRAM_BOT_TOKEN` — токен Telegram-бота

### Биржи/инфраструктура

- `HYPERLIQUID_API_KEY`, `HYPERLIQUID_API_SECRET`
- `MEXC_API_KEY`, `MEXC_API_SECRET`
- `DATABASE_URL`, `REDIS_URL`

### Сигнальный контур

- `ENABLE_SIGNALS=1` — включает realtime сигнал-пайплайн
- `FIB_SYMBOL` — рабочий символ (например `BTCUSDT`)
- `FIB_STRATEGY` — `auto_regime` или конкретная стратегия
- `ML_MIN_PROBA`, `ML_SHORT_WINDOW`, `ML_LONG_WINDOW` — пороги ML-фильтра
- `PAPER_START_EQUITY` — стартовый equity для paper-контроля DD

### Risk/Whitelist

- `RISK_ALERT_COOLDOWN_MIN` — cooldown риск-алертов
- `WHITELIST_SYMBOLS` — список разрешенных символов через запятую
- `WL_MIN_AVG_VOLUME` — минимальный объем (прокси ликвидности)
- `WL_MAX_AVG_SPREAD_PCT` — максимальный прокси-спред свечи

### News filter

- `NEWS_FILTER_ENABLED` — включение фильтра (`1`/`0`)
- `NEWS_SOURCE` — источник новостей (инфо-метка)
- `NEWS_RISK_KEYWORDS` — ключевые риск-слова
- `NEWS_BLOCK_MIN_SCORE` — порог блокировки
- `NEWS_HEADLINE` — текущий headline для оценки риска

## Работа с ботом в Telegram

### Базовый сценарий настройки

1. `/start` — открыть приветствие и основное меню
2. `/mode_menu` — выбрать режим
3. `/tf_menu` — выбрать таймфрейм
4. `/risk` — перейти в мастер-меню риска
5. `/status` — проверить итоговые настройки
6. `/readiness` — проверить готовность к live-этапу
7. `/news` — проверить параметры news-engine

### Основные команды

- `/menu` — главное меню
- `/status` — текущие параметры профиля
- `/positions` — статус позиций
- `/help` — подсказка по использованию
- `/backtest` — mini-backtest
- `/ml_report` — отчет по ML

### Команды торговли и риск-параметров

- Режим: `/mode signal_only|paper|live`
- Таймфрейм: `/set_tf 1m|5m|15m|1h|4h`
- Риск: `/set_risk <pct>`
- RR: `/set_rr <value>`
- DD: `/set_dd <pct>`
- Лимит позиций: `/set_maxpos <int>`
- SL/TP: `/set_sl <pct>`, `/set_tp <pct>`
- Закрыть 1 позицию: `/close`

## Режимы торговли и как ими пользоваться

### 1) `signal_only`

- Что делает: отправляет сигналы, без увеличения счетчика paper-позиций
- Когда использовать: мониторинг качества сигналов и ручные решения

### 2) `paper`

- Что делает: отправляет сигналы и имитирует открытие позиций (через `open_positions_count`)
- Когда использовать: безопасная обкатка стратегии и риск-настроек
- Рекомендация: начать с `risk=0.5..1.0`, `DD<=5..8`, `maxpos=1..2`

### 3) `live`

- Что делает: профиль live-готовности и финальный этап перед боевым контуром
- Перед использованием обязательно:
  - пройти `/readiness` без блокирующих пунктов
  - проверить ключи и лимиты риска
  - убедиться в корректном поведении в `paper`

## Рекомендованный порядок перехода к торговле

1. Запуск в `signal_only` и проверка стабильности сигналов
2. Переход в `paper` и проверка:
   - поведения risk/DD/maxpos
   - whitelist фильтров
   - news-risk блокировок
3. Mini-backtest по целевым активам
4. `/readiness` и только после этого переход в `live`

## Тестирование

Запуск полного набора тестов:

```powershell
python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience tests.test_news_engine -v
```

## Важно

- Это инфраструктура и автоматизация сигналов/контроля риска; не является финансовой рекомендацией.
- Перед любыми live-действиями обязательно тестируйте сценарии на `paper`.
