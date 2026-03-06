# Fibo Bot — Quick Start

Короткий сценарий, чтобы быстро поднять бота и протестировать интерфейс в Telegram.

## 1) Подготовка

```powershell
Copy-Item .env.example .env
```

В `.env` обязательно укажи:

- `TELEGRAM_BOT_TOKEN=...`

## 2) Полный перезапуск Docker (чисто)

```powershell
docker compose -f infra/docker/docker-compose.yml down --volumes --remove-orphans
docker builder prune -af
docker image prune -af
docker volume prune -f
docker network prune -f
docker compose -f infra/docker/docker-compose.yml build --no-cache
docker compose -f infra/docker/docker-compose.yml up -d
docker compose -f infra/docker/docker-compose.yml ps
```

Ожидаемо: `fib_bot_app`, `fib_bot_redis`, `fib_bot_postgres` в статусе `healthy`.

## 3) Проверка логов приложения

```powershell
docker compose -f infra/docker/docker-compose.yml logs --no-color --tail 120 app
```

Ожидаемо увидеть строку старта:

`fib_bot app started env=... mode=...`

## 4) Минимальная проверка в Telegram

В чате с ботом выполни:

1. `/start`
2. `/menu`
3. `/mode_menu` → выбери `paper`
4. `/tf_menu` → выбери `5m`
5. `/risk` → проверь подэкраны Risk/RR/DD
6. `/status`
7. `/readiness`
8. `/news`
9. `/backtest symbol=BTCUSDT timeframe=5m`

## 5) Рекомендуемые стартовые настройки (paper)

- `mode=paper`
- `risk=0.5..1.0`
- `rr=1.5..2.0`
- `dd=5..8`
- `maxpos=1..2`

## 6) Полезные команды

- `/status` — текущий профиль
- `/positions` — состояние позиций
- `/risk` — меню лимитов и пресетов
- `/readiness` — готовность к live
- `/news` — статус news engine
- `/ml_report` — качество ML-фильтра

## 7) Остановка

```powershell
docker compose -f infra/docker/docker-compose.yml down
```
