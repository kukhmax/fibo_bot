# DEVELOP.md — Детализация этапов и журнал реализации

## 1) Правила работы по подэтапам

- Работа ведется подэтапами с уникальным ID: `E<этап>.<подэтап>`.
- После завершения каждого подэтапа фиксируется запись в разделе `Журнал выполнения`.
- После записи в журнал все изменения добавляются в git и создается подробный коммит.
- После коммита выполняется push в удаленный репозиторий (GitHub) в соответствующую ветку.
- После коммита отправляется короткий отчет и вопрос: понятно ли результат и можно ли переходить дальше.
- Если подэтап не завершен полностью, он не коммитится как завершенный.
- Запись по подэтапу обязательна и должна содержать: измененные файлы, реализованную логику, команды запуска/проверки и результаты тестов.

---

## 2) Подэтапы реализации (MVP)

## Этап 0 — Подготовка инфраструктуры

- `E0.1` Создать каркас каталогов и модулей проекта.
- `E0.2` Добавить базовую конфигурацию окружений `dev/test/paper`.
- `E0.3` Добавить шаблоны `.env.example` и правила загрузки секретов.
- `E0.4` Подготовить `docker-compose` для app, redis, postgres.
- `E0.5` Добавить базовые health-check точки и smoke-проверку запуска.

## Этап 1 — Data Layer

- `E1.1` Реализовать WS-клиент Hyperliquid для trade/kline потоков.
- `E1.2` Добавить REST fallback Hyperliquid для восстановления пропусков.
- `E1.3` Реализовать candle builder для таймфреймов (дефолт 5m + настраиваемый).
- `E1.4` Реализовать адаптер MEXC как резервный источник.
- `E1.5` Добавить валидацию качества данных: gap, stale, timestamp drift.
- `E1.6` Добавить persistence слоя (кэш состояния и локальная история для бэктеста).

## Этап 2 — Telegram Core

- `E2.1` Поднять каркас Telegram-бота с маршрутизацией команд.
- `E2.2` Реализовать `/start` мастер-профиль (режим, биржа, ТФ, риск, отчет).
- `E2.3` Реализовать `/mode`, `/set_tf`, `/set_risk`, `/status`.
- `E2.4` Реализовать режимы доступа `notify_only` и `full_access`.
- `E2.5` Реализовать периодические отчеты по позициям (дефолт 1 час).
- `E2.6` Реализовать `/positions` и базовые action-кнопки.

## Этап 3 — Strategy + Regime

- `E3.1` Подключить Strategy 1: Trend Pullback.
- `E3.2` Подключить Strategy 2: Volatility Breakout.
- `E3.3` Подключить Strategy 3: Liquidity Sweep Reversal.
- `E3.4` Реализовать rule-based regime classifier.
- `E3.5` Добавить единый интерфейс сигналов и explain-поля по входам/пропускам.
- `E3.6` Добавить переключение активной стратегии по режиму рынка.

## Этап 4 — ML Filter

- `E4.1` Подготовить pipeline исторических данных для обучения.
- `E4.2` Реализовать feature engineering для ML-фильтра.
- `E4.3` Реализовать labeling и формирование train/validation датасетов.
- `E4.4` Обучить базовую модель фильтра вероятности и сохранить артефакты.
- `E4.5` Подключить инференс фильтра в signal/paper контур.
- `E4.6` Добавить отчет о качестве ML-модели в Telegram-формате.

## Этап 5 — Risk + Auto-Pause

- `E5.1` Реализовать ограничение риска на сделку (<=2%).
- `E5.2` Реализовать дневной лимит просадки (<=10%).
- `E5.3` Реализовать авто-паузу торговли до UTC 00:00.
- `E5.4` Реализовать контроль max open positions.
- `E5.5` Реализовать команды управления позицией: изменение SL/TP и закрытие.
- `E5.6` Добавить аварийные уведомления о блокировках риска.

## Этап 6 — Mini-backtest в Telegram

- `E6.1` Реализовать команду `/backtest` с выбором актива и ТФ.
- `E6.2` Реализовать загрузку 3000 свечей выбранного актива.
- `E6.3` Прогонять стратегии и ML-фильтр в mini-backtest контуре.
- `E6.4` Формировать метрики PF, DD, Winrate, R:R, Expectancy, trades.
- `E6.5` Отправлять структурированный отчет в Telegram.
- `E6.6` Добавить итоговый флаг по активу: допущен/не допущен.

## Этап 7 — Stabilization

- `E7.1` Добавить интеграционные тесты ключевых сценариев.
- `E7.2` Прогнать paper-сценарии на нескольких активах.
- `E7.3` Проверить устойчивость режимов signal_only/paper при ошибках источников.
- `E7.4` Подготовить release-note и чеклист перехода к live-этапу.
- `E7.5` Сформировать backlog пост-MVP задач (whitelist/news/live hardening).

---

## 3) Формат записи в журнал выполнения

Каждая запись в журнале оформляется по шаблону:

```text
Дата/время (UTC):
Подэтап:
Что сделано:
Какие файлы изменены:
Реализованная логика:
Команды:
Тесты:
Как проверено:
Результат:
Commit:
```

---

## 4) Журнал выполнения

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.0`  
Что сделано: Создан DEVELOP.md с детализацией всех этапов до уровня подэтапов и правилами фиксации прогресса.  
Какие файлы изменены: `DEVELOP.md`  
Реализованная логика: Введен обязательный процесс разработки по подэтапам с журналом фиксации результата.  
Команды: `git add DEVELOP.md`, `git commit -m DEVELOP_E0.0_добавлен_DEVELOP.md_с_декомпозицией_этапов_и_правилами_фиксации`  
Тесты: Неприменимо для документационного подэтапа, выполнена ручная валидация структуры.  
Как проверено: Проверена структура документа и соответствие подтвержденному PLAN.md.  
Результат: Готов процесс разработки с пошаговой фиксацией и коммит-дисциплиной.  
Commit: `b29b50a`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.0.1`  
Что сделано: Уточнены обязательные требования к журналу разработки по вашему правилу.  
Какие файлы изменены: `DEVELOP.md`  
Реализованная логика: Каждая запись теперь обязана включать реализованную логику, команды и тесты, чтобы журнал отражал полный контекст выполнения шага.  
Команды: `git add DEVELOP.md`, `git commit -m DEVELOP_E0.0.1_уточнены_правила_журнала_файлы_логика_команды_тесты`  
Тесты: Ручная проверка шаблона записи и соответствия вашему требованию.  
Как проверено: Сверка полей шаблона в разделе формата и наличия новых требований в правилах.  
Результат: DEVELOP.md приведен к формату полного инженерного лога по каждому шагу.  
Commit: `b356fab`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.1`  
Что сделано: Создан каркас каталогов и модулей проекта согласно архитектуре из PLAN.md.  
Какие файлы изменены: `core/__init__.py`, `core/config/__init__.py`, `core/data/__init__.py`, `core/features/__init__.py`, `core/regime/__init__.py`, `core/strategies/__init__.py`, `core/ml/__init__.py`, `core/risk/__init__.py`, `core/execution/__init__.py`, `core/backtest/__init__.py`, `core/bot/__init__.py`, `infra/docker/.gitkeep`, `infra/monitoring/.gitkeep`, `docs/.gitkeep`  
Реализованная логика: Подготовлена базовая модульная структура пакета `core` для последующей поэтапной реализации data/strategy/ml/risk/execution/telegram слоев, а также инфраструктурные директории для docker/monitoring и раздел документации.  
Команды: проверка структуры через `Glob("**/*")`, далее `git add`, `git commit`  
Тесты: Выполнена структурная проверка наличия всех обязательных директорий и модулей по списку этапа `E0.1`.  
Как проверено: Сверена фактическая структура репозитория с разделом архитектуры в PLAN.md, все ожидаемые каталоги присутствуют.  
Результат: Репозиторий готов к подэтапу `E0.2` с добавлением базовой конфигурации окружений.  
Commit: `6950869`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.2`  
Что сделано: Реализована базовая конфигурация окружений `dev/test/paper` с загрузчиком профилей и первичным тестовым покрытием.  
Какие файлы изменены: `core/config/__init__.py`, `core/config/models.py`, `core/config/loader.py`, `core/config/profiles/dev.json`, `core/config/profiles/test.json`, `core/config/profiles/paper.json`, `tests/test_config_loader.py`, `.gitignore`, `DEVELOP.md`  
Реализованная логика: Добавлены типизированные модели конфигурации, загрузчик JSON-профилей с валидацией окружения и три профиля окружений с согласованными параметрами бирж, риска, режима бота и ML-фильтра. Добавлен `.gitignore` с базовыми правилами игнорирования секретов, артефактов Python и технического terminal-артефакта.  
Команды: `python -m unittest tests.test_config_loader -v`, `git add DEVELOP.md core/config tests/test_config_loader.py .gitignore`, `git commit -m <сообщение>`  
Тесты: `python -m unittest tests.test_config_loader -v` — 4 теста, все успешны (загрузка dev/test/paper + проверка ошибки для неизвестного окружения).  
Как проверено: Проверена загрузка конфигов через unit-тесты и сопоставление ключевых значений требованиям из PLAN.md.  
Результат: Базовый конфиг-контур готов для подэтапа `E0.3` (шаблоны `.env` и правила секретов).  
Commit: см. `git log --oneline -n 2`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.3`  
Что сделано: Добавлены шаблон `.env.example`, модуль загрузки секретов и правила работы с секретами в документации.  
Какие файлы изменены: `core/config/__init__.py`, `core/config/secrets.py`, `.env.example`, `docs/SECRETS.md`, `tests/test_secrets_loader.py`, `DEVELOP.md`  
Реализованная логика: Реализован единый загрузчик секретов из переменных окружения и `.env` файла с приоритетом окружения, введена валидация обязательного Telegram-токена и торговых ключей Hyperliquid для режимов с требованием торговых кредов.  
Команды: `python -m unittest tests.test_config_loader tests.test_secrets_loader -v`, `git add DEVELOP.md core/config/secrets.py core/config/__init__.py .env.example docs/SECRETS.md tests/test_secrets_loader.py`, `git commit -m <сообщение>`  
Тесты: `python -m unittest tests.test_config_loader tests.test_secrets_loader -v` — 8 тестов, все успешны. Проверены загрузка из файла, приоритет переменных окружения и валидация обязательных секретов.  
Как проверено: Проверен полный прогон unit-тестов конфигурации и секретов, а также консистентность правил в `docs/SECRETS.md` и шаблоне `.env.example`.  
Результат: Подэтап `E0.3` завершен, контур секретов и шаблонов окружения готов к использованию в следующих этапах.  
Commit: см. `git log --oneline -n 3`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.4`  
Что сделано: Подготовлен Docker-контур с `docker-compose` для сервисов `app`, `redis`, `postgres` и базовым Dockerfile приложения.  
Какие файлы изменены: `infra/docker/docker-compose.yml`, `infra/docker/Dockerfile.app`, `core/bot/main.py`, `.env.example`, `DEVELOP.md`  
Реализованная логика: Добавлен контейнерный запуск приложения через `python -m core.bot.main`, инфраструктурные сервисы Redis/Postgres с volume-хранилищами, сеть `fib_bot_net`, а также опциональное подключение `.env` для локального запуска без обязательного файла.  
Команды: `python -m core.bot.main --once`, `docker compose -f infra/docker/docker-compose.yml config`, `git add DEVELOP.md infra/docker/docker-compose.yml infra/docker/Dockerfile.app core/bot/main.py .env.example`, `git commit -m <сообщение>`  
Тесты: Проверен запуск app stub командой `python -m core.bot.main --once`; проверена валидность compose-файла через `docker compose ... config`.  
Как проверено: Compose-конфигурация разворачивается корректно, сервисы и зависимости интерпретируются без ошибок, приложение стартует в локальном режиме.  
Результат: Подэтап `E0.4` завершен, инфраструктура app/redis/postgres готова к следующему шагу health-check и smoke-проверки.  
Commit: `a786b48`

Дата/время (UTC): 2026-03-05  
Подэтап: `E0.5`  
Что сделано: Реализованы health-check механизмы приложения и сервисов, а также выполнены smoke-проверки запуска и compose-конфигурации.  
Какие файлы изменены: `core/bot/health.py`, `core/bot/main.py`, `infra/docker/docker-compose.yml`, `tests/test_health_snapshot.py`, `DEVELOP.md`  
Реализованная логика: Добавлен health snapshot приложения с проверкой доступности Redis/Postgres по TCP, интегрирован CLI-флаг `--health` с JSON-ответом и кодом выхода, подключены healthcheck-блоки для `app`, `redis`, `postgres` в docker-compose и зависимости по `service_healthy`.  
Команды: `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot -v`, `python -m core.bot.main --once`, `docker compose -f infra/docker/docker-compose.yml config`, `git add DEVELOP.md core/bot/health.py core/bot/main.py infra/docker/docker-compose.yml tests/test_health_snapshot.py`, `git commit -m <сообщение>`  
Тесты: Прогнаны 10 unit-тестов (конфиги, секреты, health snapshot), все успешны; дополнительно проверен локальный старт app stub и успешный рендер итогового compose-конфига с healthcheck секциями.  
Как проверено: Результаты unit-тестов подтверждают корректность логики health snapshot; `docker compose ... config` подтверждает валидную структуру и зависимости healthcheck; запуск `--once` подтверждает отсутствие регрессий старта.  
Результат: Подэтап `E0.5` завершен, проект готов к переходу к этапу Data Layer (`E1`).  
Commit: `c2b6722`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1`  
Что сделано: Реализован базовый Data Layer с потоковой обработкой тиков, построением свечей, REST fallback и резервом на MEXC.  
Какие файлы изменены: `core/data/__init__.py`, `core/data/models.py`, `core/data/candle_builder.py`, `core/data/quality.py`, `core/data/rest_client.py`, `core/data/websocket_client.py`, `tests/test_candle_builder.py`, `tests/test_data_quality.py`, `tests/test_data_fallback.py`, `DEVELOP.md`  
Реализованная логика: Добавлены модели `Tick/Candle`, `CandleBuilder` для realtime агрегации, `validate_candle_sequence` для контроля качества, Hyperliquid WS parser и orchestrator со stale-детекцией, а также загрузчик исторических свечей с fallback Hyperliquid→MEXC.  
Команды: `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback -v`, `git add DEVELOP.md core/data tests/test_candle_builder.py tests/test_data_quality.py tests/test_data_fallback.py`, `git commit -m <сообщение>`  
Тесты: Выполнено 17 unit-тестов, все успешны; покрыты сценарии агрегации свечей, валидации качества, stale WS и REST fallback.  
Как проверено: Полный тестовый прогон подтвердил отсутствие регрессий в конфигурации/health-контуре и корректную работу новых модулей Data Layer.  
Результат: Этап `E1` закрывает базовый каркас data ingestion и подготавливает почву для подключения реальных WS-каналов и funding/OI в следующем подэтапе.  
Commit: `028d465`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.1`  
Что сделано: Реализован рантайм WS-клиента Hyperliquid с подписками на trade/kline и автоматическим восстановлением соединения.  
Какие файлы изменены: `core/data/websocket_client.py`, `core/data/__init__.py`, `tests/test_ws_runtime.py`, `DEVELOP.md`  
Реализованная логика: Добавлены `HyperliquidWsClient` и `ReconnectPolicy` с reconnect/backoff/jitter, heartbeat timeout watchdog через `asyncio.wait_for`, отправка подписок `trades` и `candle`, а также callback-обработчик входящих тиков.  
Команды: `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime -v`, `git add DEVELOP.md core/data/websocket_client.py core/data/__init__.py tests/test_ws_runtime.py`, `git commit -m <сообщение>`  
Тесты: Прогнаны 20 unit-тестов, все успешны; дополнительно покрыты сценарии reconnect после дисконнекта, heartbeat timeout и корректная отправка WS-подписок.  
Как проверено: Полный прогон тестов подтвердил отсутствие регрессий и корректную работу WS-рантайма с policy-based восстановлением соединения.  
Результат: Подэтап `E1.1` завершен, контур live WS ingestion готов для подключения REST восстановления пропусков на уровне рантайма (`E1.2`).  
Commit: `1c8bf37`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.2`  
Что сделано: Интегрировано REST-восстановление пропусков в рантайм WS-клиента после реконнекта.  
Какие файлы изменены: `core/data/websocket_client.py`, `tests/test_ws_runtime.py`, `DEVELOP.md`  
Реализованная логика: В `HyperliquidWsClient` добавлены `rest_data`, `on_backfill` и механизм backfill на реконнекте; реализована оценка окна пропуска по таймфрейму, фильтрация восстановленных свечей по timestamp и доставка backfill-пакета через callback перед продолжением live-потока.  
Команды: `python -m unittest tests.test_ws_runtime -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime -v`, `git add DEVELOP.md core/data/websocket_client.py tests/test_ws_runtime.py`, `git commit -m <сообщение>`  
Тесты: Прогнаны 21 unit-тест, все успешны; добавлен тест сценария восстановления пропуска после реконнекта с проверкой вызова REST backfill и фильтрации свечей.  
Как проверено: Подтверждена корректность восстановления gap-данных и отсутствие регрессий по всем ранее реализованным модулям.  
Результат: Подэтап `E1.2` завершен, WS-рантайм теперь восстанавливает пропуски через REST и готов к расширению источников данных.  
Commit: `dcf7e6d`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.3`  
Что сделано: Реализован realtime candle pipeline с дефолтным ТФ 5m и поддержкой настраиваемого timeframe.  
Какие файлы изменены: `core/data/pipeline.py`, `core/data/websocket_client.py`, `core/data/__init__.py`, `tests/test_realtime_candle_pipeline.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `RealtimeCandlePipeline`, который принимает тик-поток и backfill-свечи, агрегирует их в `CandleBuilder`, эмитит закрытые свечи через callback и подавляет дубликаты по `open_time_ms`; в WS-клиенте зафиксирован дефолтный timeframe `5m`.  
Команды: `python -m unittest tests.test_realtime_candle_pipeline tests.test_ws_runtime -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline -v`, `git add DEVELOP.md core/data/pipeline.py core/data/websocket_client.py core/data/__init__.py tests/test_realtime_candle_pipeline.py`, `git commit -m <сообщение>`  
Тесты: Прогнаны 25 unit-тестов, все успешны; добавлены проверки дефолтного 5m, настраиваемого timeframe, эмита закрытых свечей и подавления backfill-дубликатов.  
Как проверено: Подтверждена корректная работа realtime candle pipeline и отсутствие регрессий по ранее реализованным модулям Data Layer.  
Результат: Подэтап `E1.3` завершен, базовый pipeline построения свечей для live-потока готов к подключению адаптера резервной биржи (`E1.4`).  
Commit: `ac023fe`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.4`  
Что сделано: Реализован live WS-адаптер MEXC и переключение на резервный источник при деградации primary-runtime.  
Какие файлы изменены: `core/data/websocket_client.py`, `core/data/pipeline.py`, `core/data/__init__.py`, `tests/test_mexc_ws_adapter.py`, `DEVELOP.md`  
Реализованная логика: Добавлены `MexcWebSocketParser` и `MexcWsClient` с подписками `sub.deal/sub.kline`, а также `PrimaryBackupWsClient` для последовательного failover primary→backup; `RealtimeCandlePipeline` обновлен для работы через runtime-протокол и подключения MEXC как backup по умолчанию.  
Команды: `python -m unittest tests.test_mexc_ws_adapter tests.test_ws_runtime tests.test_realtime_candle_pipeline -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter -v`, `git add DEVELOP.md core/data/websocket_client.py core/data/pipeline.py core/data/__init__.py tests/test_mexc_ws_adapter.py`, `git commit -m <сообщение>`  
Тесты: Прогнаны 28 unit-тестов, все успешны; добавлены проверки MEXC parser/client и сценария переключения на backup runtime.  
Как проверено: Подтверждена корректность работы адаптера MEXC и отсутствие регрессий в существующем data/WS pipeline.  
Результат: Подэтап `E1.4` завершен, резервный live-источник данных MEXC подключен к runtime-контуру.  
Commit: `5d4b554`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.5`  
Что сделано: Добавлен runtime-контур валидации качества данных для gap/stale/timestamp drift и интегрирован в realtime pipeline.  
Какие файлы изменены: `core/data/quality.py`, `core/data/pipeline.py`, `core/data/__init__.py`, `tests/test_data_quality.py`, `tests/test_realtime_candle_pipeline.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `RuntimeDataQualityMonitor` с проверками gap/overlap по свечам, stale-потока по таймауту и timestamp drift для tick/candle; в `RealtimeCandlePipeline` добавлены `on_quality`, `quality_monitor` и метод `health_report` для runtime-репортов качества.  
Команды: `python -m unittest tests.test_data_quality tests.test_realtime_candle_pipeline -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter -v`, `git add DEVELOP.md core/data/quality.py core/data/pipeline.py core/data/__init__.py tests/test_data_quality.py tests/test_realtime_candle_pipeline.py`, `git commit -m <сообщение>`  
Тесты: Прогнан 31 unit-тест, все успешны; добавлены сценарии runtime-детекции gap/stale/drift и эмита quality-report в pipeline.  
Как проверено: Подтверждена корректность новых quality-checks и отсутствие регрессий в Data Layer и WS/runtime контуре.  
Результат: Подэтап `E1.5` завершен, runtime-контроль качества данных готов к использованию в алертинге и risk-контуре.  
Commit: `962055e`

Дата/время (UTC): 2026-03-05  
Подэтап: `E1.6`  
Что сделано: Реализован persistence-слой с кэшем состояния и локальной историей свечей для бэктеста.  
Какие файлы изменены: `core/data/persistence.py`, `core/data/pipeline.py`, `core/data/__init__.py`, `core/backtest/history.py`, `core/backtest/__init__.py`, `tests/test_persistence.py`, `tests/test_realtime_candle_pipeline.py`, `DEVELOP.md`  
Реализованная логика: Добавлены `StateCache` и `LocalCandleHistory`; `RealtimeCandlePipeline` сохраняет эмитированные свечи в локальную историю, кэширует `last_emitted_open_time_ms` и восстанавливает это состояние после рестарта; добавлен загрузчик локальной истории `load_local_backtest_candles` для backtest-контура.  
Команды: `python -m unittest tests.test_persistence tests.test_realtime_candle_pipeline tests.test_data_quality -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence -v`, `git add DEVELOP.md core/data/persistence.py core/data/pipeline.py core/data/__init__.py core/backtest/history.py core/backtest/__init__.py tests/test_persistence.py tests/test_realtime_candle_pipeline.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 35 unit-тестов, все успешны; добавлены проверки записи/чтения state cache, локальной истории, восстановления состояния pipeline и загрузки истории для backtest.  
Как проверено: Подтверждена корректность persistence-контура и отсутствие регрессий в существующих data/ws/runtime модулях.  
Результат: Подэтап `E1.6` завершен, кэш состояния и локальная история готовы для использования в backtest и восстановлении рантайма.  
Commit: `f445f3f`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.1`  
Что сделано: Поднят каркас Telegram Core с маршрутизацией команд и runtime-контуром обработки входящих апдейтов.  
Какие файлы изменены: `core/bot/router.py`, `core/bot/runtime.py`, `core/bot/commands.py`, `core/bot/main.py`, `core/bot/__init__.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлены `CommandRouter` и `CommandContext` с async-dispatch по slash-командам, `TelegramBotRuntime` с протоколом transport для polling/send, а также дефолтные команды `/start`, `/help`, `/status`; в CLI добавлен флаг `--commands` для вывода зарегистрированных маршрутов.  
Команды: `python -m unittest tests.test_bot_router tests.test_health_snapshot -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router -v`, `git add DEVELOP.md core/bot/router.py core/bot/runtime.py core/bot/commands.py core/bot/main.py core/bot/__init__.py tests/test_bot_router.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 39 unit-тестов, все успешны; добавлены проверки роутинга команд, unknown-сценария, дефолтных хендлеров и runtime-обработки апдейтов.  
Как проверено: Подтверждена корректность Telegram-каркаса и отсутствие регрессий в существующих модулях проекта.  
Результат: Подэтап `E2.1` завершен, базовая маршрутизация Telegram-команд готова для последующих подэтапов профиля и управляющих команд.  
Commit: `4ecff93`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.2`  
Что сделано: Реализован `/start` мастер-профиль с настройкой режима, биржи, таймфрейма, риска и интервала отчета по пользователю.  
Какие файлы изменены: `core/bot/profile.py`, `core/bot/commands.py`, `core/bot/__init__.py`, `tests/test_bot_router.py`, `tests/test_bot_profile_store.py`, `DEVELOP.md`  
Реализованная логика: Добавлены `TelegramUserProfile` и `TelegramUserProfileStore` с персистентным хранением в `StateCache`; `/start` теперь создает/обновляет пользовательский профиль через параметры `mode/exchange/timeframe/risk/report`, валидирует значения и возвращает текущее состояние профиля; `/status` отображает персональные настройки пользователя из сохраненного профиля.  
Команды: `python -m unittest tests.test_bot_profile_store tests.test_bot_router -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store -v`, `git add DEVELOP.md core/bot/profile.py core/bot/commands.py core/bot/__init__.py tests/test_bot_router.py tests/test_bot_profile_store.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 43 unit-теста, все успешны; добавлены проверки дефолтного создания профиля, персистентности между инстансами store, обновления `/start` и валидации невалидных параметров.  
Как проверено: Подтверждена корректность master-profile контура и отсутствие регрессий в существующих data/bot/runtime модулях.  
Результат: Подэтап `E2.2` завершен, пользовательский профиль Telegram готов для дальнейших управляющих команд `/mode`, `/set_tf`, `/set_risk`, `/status`.  
Commit: `6bf74f3`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.3`  
Что сделано: Реализованы отдельные команды управления профилем `/mode`, `/set_tf`, `/set_risk` и обновлен статусный вывод `/status`.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлены хендлеры команд `/mode`, `/set_tf`, `/set_risk` с валидацией аргументов и персистентным сохранением в пользовательский профиль; `/status` отражает обновленные значения профиля, help автоматически показывает расширенный набор команд.  
Команды: `python -m unittest tests.test_bot_router tests.test_bot_profile_store -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store -v`, `git add DEVELOP.md core/bot/commands.py tests/test_bot_router.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 47 unit-тестов, все успешны; добавлены проверки обновления mode/timeframe/risk через отдельные команды и валидации невалидного риска.  
Как проверено: Подтверждена корректность команд E2.3 и отсутствие регрессий в существующих модулях проекта.  
Результат: Подэтап `E2.3` завершен, управление профилем через `/mode`, `/set_tf`, `/set_risk`, `/status` готово к использованию.  
Commit: `ecbd816`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.3 UX`  
Что сделано: Добавлена нижняя reply-клавиатура Telegram с кнопками, дублирующими команды и настройки, чтобы не вводить команды вручную.  
Какие файлы изменены: `core/bot/router.py`, `core/bot/runtime.py`, `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: `RouteResult` расширен полем `reply_keyboard`, в `CommandRouter` добавлена поддержка общей клавиатуры и авто-прокидка markup во все ответы; в runtime `send_text` принимает `reply_keyboard`; в `commands.py` настроена клавиатура с кнопками `/start`, `/status`, `/help`, пресетами `/mode`, `/set_tf`, `/set_risk`.  
Команды: `python -m unittest tests.test_bot_router -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store -v`, `git add DEVELOP.md core/bot/router.py core/bot/runtime.py core/bot/commands.py tests/test_bot_router.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 47 unit-тестов, все успешны; добавлены проверки наличия reply-клавиатуры в ответах и передачи клавиатуры через runtime transport.  
Как проверено: Подтверждена корректность UX-кнопок и отсутствие регрессий в bot/data/runtime контуре.  
Результат: Нижние кнопки готовы и дублируют команды/настройки в ответах бота.  
Commit: `a720140`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.3 Runtime API`  
Что сделано: Подключен реальный Telegram Bot API transport и запущен polling runtime в entrypoint бота.  
Какие файлы изменены: `core/bot/telegram_transport.py`, `core/bot/main.py`, `core/bot/__init__.py`, `tests/test_telegram_transport.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `TelegramApiTransport` на `urllib` для `getUpdates/sendMessage` с поддержкой `reply_markup` для нижней клавиатуры; `main.run` теперь создает transport и `TelegramBotRuntime`, запускает polling-цикл через `asyncio`, а в режиме `--once` выполняет один проход обработки.  
Команды: `python -m unittest tests.test_telegram_transport tests.test_bot_router -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport -v`, `git add DEVELOP.md core/bot/telegram_transport.py core/bot/main.py core/bot/__init__.py tests/test_telegram_transport.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 49 unit-тестов, все успешны; добавлены проверки парсинга `getUpdates` и формирования payload `sendMessage` с reply-клавиатурой.  
Как проверено: Подтверждена корректность Bot API интеграции и отсутствие регрессий в существующих модулях проекта.  
Результат: Бот готов работать с реальным Telegram API и показывать нижние кнопки в чате без ручного ввода команд.  
Commit: `5ade3c8`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.4`  
Что сделано: Внедрен режим доступа `notify_only`: любые команды изменения профиля (`/start` с аргументами, `/mode`, `/set_tf`, `/set_risk`) блокируются, ответы содержат уведомление о режиме.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлена проверка `access_mode` из окруженческого конфига; при значении `notify_only` все write-команды возвращают информативное сообщение и не изменяют сохранённый профиль.  
Команды: `python -m unittest tests.test_bot_router -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport -v`, `git add DEVELOP.md core/bot/commands.py tests/test_bot_router.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 50 unit-тестов, все успешны; добавлена проверка блокировки обновлений профиля в режиме `notify_only`.  
Как проверено: Убедились, что настройки не меняются и статус отражает исходные значения при `notify_only`.  
Результат: Подэтап `E2.4` завершен, ограничение на изменение настроек действует согласно конфигурации доступа.  
Commit: `4a3636c`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.3`  
Что сделано: Реализована стратегия Liquidity Sweep Reversal и подключена опция выбора через `FIB_STRATEGY=liquidity_sweep`.  
Какие файлы изменены: `core/strategies/liquidity_sweep_reversal.py`, `core/strategies/__init__.py`, `core/bot/main.py`, `tests/test_strategy_liquidity_sweep.py`, `DEVELOP.md`  
Реализованная логика: BUY при пробое предыдущего low и возврате выше него с бычьим закрытием; SELL при пробое предыдущего high и возврате ниже него с медвежьим закрытием. Интеграция выполняется только при `ENABLE_SIGNALS=1`.  
Команды: `python -m unittest tests.test_strategy_liquidity_sweep -v`, полный регресс `python -m unittest ... -v`  
Тесты: Прогнано 57 unit-тестов, все успешны; добавлены юнит-тесты стратегии.  
Как проверено: Поведение подтверждено тестами; опция выбора стратегии сохраняет обратную совместимость.  
Результат: Подэтап `E3.3` завершен, добавлена третья стратегия в выбор.  
Commit: `b1a2e42`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.5`  
Что сделано: Реализован периодический отчет по позициям с интервалом из профиля пользователя (`position_report_minutes`, по умолчанию 60).  
Какие файлы изменены: `core/bot/runtime.py`, `core/bot/reporter.py`, `core/bot/main.py`, `tests/test_reports_scheduler.py`, `DEVELOP.md`  
Реализованная логика: В `TelegramBotRuntime.process_once` добавлен шедулер, который просматривает сохраненные профили и отправляет отчет при наступлении времени; состояние отправки хранится в `runtime/report_last_sent.json`, формирование текста отчета через `PositionReporter` (пока заглушка без реальных позиций).  
Команды: `python -m unittest tests.test_reports_scheduler -v`, `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler -v`, `git add DEVELOP.md core/bot/runtime.py core/bot/reporter.py core/bot/main.py tests/test_reports_scheduler.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 51 unit-тест, все успешны; добавлен тест на отправку отчета при наступлении срока.  
Как проверено: Проверена отправка отчета без входящих апдейтов и отсутствие регрессий.  
Результат: Подэтап `E2.5` завершен, отчеты рассылаются автоматически по заданному интервалу.  
Commit: `94e4f76`

Дата/время (UTC): 2026-03-05  
Подэтап: `E2.6`  
Что сделано: Добавлена команда `/positions` и базовые action-кнопки inline для обновления отчета. Поддержаны `inline_keyboard` и обработка `callback_query` в транспортном слое.  
Какие файлы изменены: `core/bot/commands.py`, `core/bot/router.py`, `core/bot/runtime.py`, `core/bot/telegram_transport.py`, `tests/test_telegram_transport.py`, `DEVELOP.md`  
Реализованная логика: Хендлер `/positions` возвращает текст отчета и inline-кнопку «Обновить» с `callback_data=/positions`; router научился принимать словарь `{text, inline_keyboard}`, runtime и transport передают inline-клавиатуры и парсят `callback_query` в команды.  
Команды: `python -m unittest tests.test_telegram_transport tests.test_bot_router -v`, полный регресс `python -m unittest ... -v`; `git add DEVELOP.md core/bot/commands.py core/bot/router.py core/bot/runtime.py core/bot/telegram_transport.py tests/test_telegram_transport.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 53 unit-теста, все успешны; добавлены проверки inline-клавиатуры и парсинга `callback_query`.  
Как проверено: Нажатие inline-кнопки исполняет `/positions` через `callback_query`, клавиатуры доставляются в `sendMessage`.  
Результат: Подэтап `E2.6` завершен, команда `/positions` и базовые action-кнопки доступны пользователю.  
Commit: `bebcfaa`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.1`  
Что сделано: Подключена базовая стратегия Trend Pullback и опциональная рассылка сигналов в режимах `signal_only` и `paper` (включается переменной окружения `ENABLE_SIGNALS=1`).  
Какие файлы изменены: `core/strategies/__init__.py`, `core/strategies/trend_pullback.py`, `core/bot/main.py`, `DEVELOP.md`  
Реализованная логика: Реализован простейший детектор тренд-ресюма по трем последовательным закрытиям; при включении опции запускается pipeline свечей и при сигнале выполняется broadcast по пользователям в разрешенных режимах. Символ задается `FIB_SYMBOL`, таймфрейм — из профиля окружения.  
Команды: `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler -v`, `git add DEVELOP.md core/strategies core/bot/main.py`, `git commit -m <сообщение>`  
Тесты: Прогнано 53 unit-теста, все успешны; стратегия включается только при `ENABLE_SIGNALS=1`, поэтому регрессия отсутствует.  
Как проверено: Проверена сборка и запуск тестов; интеграция стратегии законтурена флагом окружения.  
Результат: Подэтап `E3.1` завершен, стратегический контур подключен в режиме сигналов.  
Commit: `2203a93`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.2`  
Что сделано: Реализована стратегия Volatility Breakout и выбор стратегии через переменную окружения `FIB_STRATEGY` (`trend_pullback`|`volatility_breakout`).  
Какие файлы изменены: `core/strategies/volatility_breakout.py`, `core/strategies/__init__.py`, `core/bot/main.py`, `tests/test_strategy_volatility_breakout.py`, `DEVELOP.md`  
Реализованная логика: BUY при закрытии выше предыдущего high и зеленой свече; SELL при закрытии ниже предыдущего low и красной свече. В `main.py` выбранная стратегия подключается к realtime-пайплайну при `ENABLE_SIGNALS=1`.  
Команды: `python -m unittest tests.test_strategy_volatility_breakout -v`, полный регресс `python -m unittest ... -v`  
Тесты: Прогнано 55 unit-тестов, все успешны; добавлены юнит-тесты стратегии.  
Как проверено: Стратегия изолирована unit-тестами; интеграция включается только флагом окружения.  
Результат: Подэтап `E3.2` завершен, доступен выбор действующей стратегии.  
Commit: `8448f7c`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.3`  
Что сделано: Реализована стратегия Liquidity Sweep Reversal и подключен выбор через `FIB_STRATEGY=liquidity_sweep`.  
Какие файлы изменены: `core/strategies/liquidity_sweep_reversal.py`, `core/strategies/__init__.py`, `core/bot/main.py`, `tests/test_strategy_liquidity_sweep.py`, `DEVELOP.md`  
Реализованная логика: BUY при пробое предыдущего low и возврате выше него с бычьим закрытием; SELL при пробое предыдущего high и возврате ниже него с медвежьим закрытием.  
Команды: `python -m unittest tests.test_strategy_liquidity_sweep -v`, полный регресс `python -m unittest ... -v`  
Тесты: Прогнано 57 unit-тестов, все успешны; добавлены юнит-тесты стратегии.  
Как проверено: Поведение подтверждено тестами, выбор стратегии через переменную окружения работает совместно с текущим контуром сигналов.  
Результат: Подэтап `E3.3` завершен, добавлена третья стратегия в выбор.  
Commit: `8448f7c`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.4`  
Что сделано: Реализован rule-based regime classifier для определения рыночного режима по окну свечей.  
Какие файлы изменены: `core/regime/classifier.py`, `core/regime/__init__.py`, `tests/test_regime_classifier.py`, `DEVELOP.md`  
Реализованная логика: Классификатор возвращает `unknown|range|trend_up|trend_down|volatile` на основе тренд-движения, realized volatility и среднего intrabar spread, а также confidence и explanation.  
Команды: `python -m unittest tests.test_regime_classifier -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier -v`  
Тесты: Прогнано 62 unit-теста, все успешны; добавлены тесты на все режимы классификации.  
Как проверено: Unit-тесты подтверждают корректную классификацию режимов и отсутствие регрессий во всех существующих модулях.  
Результат: Подэтап `E3.4` завершен, режим рынка доступен для дальнейшего переключения стратегий и explain-полей.  
Commit: `b1a2e42`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.5`  
Что сделано: Введен единый интерфейс сигналов `StrategyDecision` и explain-поля как для входов, так и для пропусков.  
Какие файлы изменены: `core/strategies/signal.py`, `core/strategies/trend_pullback.py`, `core/strategies/volatility_breakout.py`, `core/strategies/liquidity_sweep_reversal.py`, `core/strategies/__init__.py`, `core/bot/main.py`, `tests/test_strategy_trend_pullback.py`, `tests/test_strategy_volatility_breakout.py`, `tests/test_strategy_liquidity_sweep.py`, `DEVELOP.md`  
Реализованная логика: Все стратегии возвращают `StrategyDecision(strategy, action, direction, explain)`; `action=entry|skip`, `explain` всегда заполнен. В signal runtime рассылка идет только по `entry`, но explain сохранен и для skip-решений в едином контракте.  
Команды: `python -m unittest tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier -v`  
Тесты: Прогнано 64 unit-теста, все успешны; обновлены тесты стратегий и добавлен отдельный тест для Trend Pullback.  
Как проверено: Подтверждена совместимость стратегий через единый контракт, а также отсутствие регрессий в существующих модулях.  
Результат: Подэтап `E3.5` завершен, explain-контур для входов/пропусков унифицирован.  
Commit: `9c223ae`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E3.6`  
Что сделано: Добавлено переключение активной стратегии по рыночному режиму (`auto_regime`) с использованием классификатора режимов.  
Какие файлы изменены: `core/strategies/selector.py`, `core/strategies/__init__.py`, `core/bot/main.py`, `tests/test_strategy_selector.py`, `DEVELOP.md`  
Реализованная логика: В режиме `FIB_STRATEGY=auto_regime` выбор выполняется по метке режима (`volatile`→`volatility_breakout`, `trend_*`→`trend_pullback`, `range`→`liquidity_sweep`, иначе fallback). В уведомление добавлены поля `regime` и `confidence`. Ручной выбор стратегии через `FIB_STRATEGY` сохранен.  
Команды: `python -m unittest tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier -v`  
Тесты: Прогнано 68 unit-тестов, все успешны; добавлены тесты селектора стратегий.  
Как проверено: Проверена корректная маршрутизация режим→стратегия и отсутствие регрессий во всем проекте.  
Результат: Подэтап `E3.6` завершен, динамический выбор стратегии по режиму рынка включен.  
Commit: `24222f4`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.1`  
Что сделано: Реализован pipeline подготовки исторических свечей для обучения с объединением локальной истории и REST fallback.  
Какие файлы изменены: `core/ml/history_pipeline.py`, `core/ml/__init__.py`, `tests/test_ml_history_pipeline.py`, `DEVELOP.md`  
Реализованная логика: `HistoricalTrainingDataPipeline` загружает local history, при нехватке свечей добирает данные через `MultiExchangeHistoricalData.fetch_with_fallback`, объединяет ряды с дедупликацией по `open_time_ms` (локальные свечи имеют приоритет), сортирует и возвращает tail по `limit`.  
Команды: `python -m unittest tests.test_ml_history_pipeline -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline -v`  
Тесты: Прогнано 71 unit-тест, все успешны; добавлены тесты сценариев local-only, remote fallback + dedup и limit-tail.  
Как проверено: Подтверждена корректная сборка train-history без дублей и отсутствие регрессий во всех существующих модулях.  
Результат: Подэтап `E4.1` завершен, базовый источник исторических данных для обучения готов.  
Commit: `39d92c1`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.2`  
Что сделано: Реализован feature pipeline и сборка train-ready датасета для ML.  
Какие файлы изменены: `core/features/dataset_builder.py`, `core/features/__init__.py`, `core/ml/dataset_builder.py`, `core/ml/__init__.py`, `tests/test_feature_dataset_builder.py`, `tests/test_ml_dataset_builder.py`, `DEVELOP.md`  
Реализованная логика: `FeatureDatasetBuilder` формирует признаки (`ret_1`, `range_pct`, `body_pct`, `sma_ratio`, `volume`), рассчитывает label по горизонту и порогу, выполняет train/validation split. `MlTrainDatasetBuilder` связывает history pipeline и feature builder в единый train-ready контур.  
Команды: `python -m unittest tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_history_pipeline -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder -v`  
Тесты: Прогнано 74 unit-теста, все успешны; добавлены тесты генерации фичей, split и интеграции ML dataset builder.  
Как проверено: Подтверждены корректные признаки, бинарные target-labels и совместимость нового контура со всем проектом без регрессий.  
Результат: Подэтап `E4.2` завершен, train-ready датасет формируется автоматически из historical pipeline.  
Commit: `08006b9`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.3`  
Что сделано: Реализован отдельный labeling-модуль и выделено формирование train/validation датасетов в ML-слое.  
Какие файлы изменены: `core/ml/labeling.py`, `core/ml/train_validation.py`, `core/features/dataset_builder.py`, `core/ml/__init__.py`, `tests/test_ml_labeling.py`, `DEVELOP.md`  
Реализованная логика: `BinaryOutcomeLabeler` рассчитывает future-return и бинарный label по горизонту/порогу; `split_train_validation` выполняет стабильное разбиение train/validation. Feature builder переиспользует эти компоненты вместо встроенной логики labeling/split.  
Команды: `python -m unittest tests.test_ml_labeling tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_history_pipeline -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling -v`  
Тесты: Прогнано 76 unit-тестов, все успешны; добавлены тесты labeling и train/validation split.  
Как проверено: Подтверждена корректность таргет-меток, согласованное разбиение выборок и отсутствие регрессий в существующем контуре.  
Результат: Подэтап `E4.3` завершен, labeling и dataset split вынесены в отдельные переиспользуемые компоненты.  
Commit: `e79de69`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.4`  
Что сделано: Обучение базовой модели ML-фильтра вынесено в отдельный training pipeline с сохранением артефактов.  
Какие файлы изменены: `core/ml/model.py`, `core/ml/trainer.py`, `core/ml/artifacts.py`, `core/ml/training_pipeline.py`, `core/ml/__init__.py`, `tests/test_ml_training.py`, `tests/test_ml_labeling.py`, `tests/test_ml_history_pipeline.py`, `tests/test_ml_dataset_builder.py`, `DEVELOP.md`  
Реализованная логика: Добавлена базовая вероятностная модель (`BaselineProbabilityModel`), trainer на градиентном шаге для бинарной классификации, хранилище артефактов `runtime/ml/baseline_model.json` и orchestration-класс `MlTrainingPipeline` для цепочки dataset→train→save.  
Команды: `python -m unittest tests.test_ml_training tests.test_ml_labeling tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_history_pipeline -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training -v`  
Тесты: Прогнано 79 unit-тестов, все успешны; добавлены тесты обучения, сохранения/загрузки артефактов и end-to-end training pipeline.  
Как проверено: Подтверждено, что модель обучается на простом разделимом наборе, сериализуется в артефакт и загружается обратно без потери структуры.  
Результат: Подэтап `E4.4` завершен, базовая ML-модель и сохранение артефактов готовы для дальнейшего инференса.  
Commit: `cdfe368`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.5`  
Что сделано: Подключен инференс ML-фильтра в signal/paper контур рассылки сигналов.  
Какие файлы изменены: `core/ml/inference.py`, `core/bot/main.py`, `tests/test_ml_inference.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `MlSignalFilter`, который загружает артефакт модели и оценивает текущий сигнал по вероятности (`ML_MIN_PROBA`). В runtime сигналы `entry` дополнительно фильтруются по ML, а в уведомление добавляется `ml_prob`. При отсутствии модели или нехватке окна свечей фильтр не блокирует сигнал.  
Команды: `python -m unittest tests.test_ml_inference tests.test_ml_training tests.test_ml_labeling tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_history_pipeline -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference -v`  
Тесты: Прогнано 81 unit-тест, все успешны; добавлены тесты feature extraction для инференса и пороговой фильтрации сигналов.  
Как проверено: Подтверждена загрузка артефактов модели, корректный расчет `ml_prob` и блокировка/пропуск сигналов по threshold без регрессий в остальном проекте.  
Результат: Подэтап `E4.5` завершен, ML-инференс встроен в signal/paper контур.  
Commit: `d9371b9`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E4.6`  
Что сделано: Добавлен Telegram-отчет качества ML-модели через команду `/ml_report`.  
Какие файлы изменены: `core/bot/reporter.py`, `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `MlQualityReporter`, который читает `runtime/ml/baseline_model.json` и формирует отчет с `train_accuracy`, `validation_accuracy`, размерами выборок и списком признаков. В роутер добавлена команда `/ml_report` и кнопка быстрого вызова. При отсутствии артефакта возвращается корректный fallback `artifact=not_found`.  
Команды: `python -m unittest tests.test_bot_router tests.test_ml_inference tests.test_ml_training -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference -v`  
Тесты: Прогнано 83 unit-теста, все успешны; добавлены тесты команды `/ml_report` для сценариев c/без артефакта.  
Как проверено: Подтвержден корректный Telegram-формат ML-отчета и стабильная работа новых команд без регрессий.  
Результат: Подэтап `E4.6` завершен, отчет о качестве ML-модели доступен в Telegram-формате.  
Commit: `6825e78`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E5.1`  
Что сделано: Реализовано системное ограничение риска на сделку `<=2%` через отдельный `RiskManager` и runtime-enforcement.  
Какие файлы изменены: `core/risk/manager.py`, `core/risk/__init__.py`, `core/config/loader.py`, `core/bot/commands.py`, `core/bot/main.py`, `tests/test_risk_manager.py`, `tests/test_bot_router.py`, `tests/test_config_loader.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `RiskManager` с валидацией `risk_per_trade_pct` в диапазоне `0.1..2.0`, расчетом risk amount и position size. В `loader` добавлена валидация профиля на старте, в `/set_risk` используется единый risk-check, в `signal/paper` runtime добавлен runtime-check профиля перед отправкой сигнала (с блокировкой некорректного риска).  
Команды: `python -m unittest tests.test_risk_manager tests.test_bot_router tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager -v`  
Тесты: Прогнано 87 unit-тестов, все успешны; добавлен отдельный тестовый набор для `RiskManager`.  
Как проверено: Подтверждена единая risk-политика в конфиге, командах профиля и runtime-контуре сигналов без регрессий по проекту.  
Результат: Подэтап `E5.1` завершен, ограничение риска на сделку `<=2%` enforced на уровне системы.  
Commit: `338ae30`

---

Дата/время (UTC): 2026-03-05  
Подэтап: `E5.2`  
Что сделано: Реализован дневной лимит просадки `<=10%` с блокировкой сигналов в runtime.  
Какие файлы изменены: `core/risk/drawdown.py`, `core/risk/__init__.py`, `core/config/loader.py`, `core/bot/main.py`, `tests/test_risk_drawdown.py`, `tests/test_config_loader.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `DailyDrawdownGuard`, который ведет дневное состояние equity по UTC-дню и считает drawdown относительно дневного старта. При превышении порога `max_daily_drawdown_pct` (из конфига, max 10) отправка новых сигналов для пользователя блокируется. В конфиг-лоадере добавлена валидация диапазона `max_daily_drawdown_pct` в пределах `(0..10]`.  
Команды: `python -m unittest tests.test_risk_manager tests.test_risk_drawdown tests.test_bot_router tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 90 unit-тестов, все успешны; добавлены тесты сценариев daily drawdown guard.  
Как проверено: Подтверждены корректный расчет дневной просадки, блокировка при превышении лимита и отсутствие регрессий во всех модулях.  
Результат: Подэтап `E5.2` завершен, дневной лимит просадки `<=10%` enforced в signal/paper runtime.  
Commit: `608b81b`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.settings`  
Что сделано: Добавлена настройка risk, RR и лимита дневной просадки напрямую из Telegram-бота.  
Какие файлы изменены: `core/bot/profile.py`, `core/bot/commands.py`, `core/bot/main.py`, `core/bot/reporter.py`, `core/risk/drawdown.py`, `tests/test_bot_router.py`, `tests/test_bot_profile_store.py`, `tests/test_config_loader.py`, `DEVELOP.md`  
Реализованная логика: В профиль добавлены поля `rr_ratio` и `max_daily_drawdown_pct`; в Telegram добавлены команды `/set_rr` и `/set_dd`, а также быстрые кнопки. Команды `/start` и `/status` расширены новыми параметрами. Runtime применяет пользовательский `max_daily_drawdown_pct` при проверке drawdown, в сигнальные сообщения добавлен `rr`.  
Команды: `python -m unittest tests.test_bot_profile_store tests.test_bot_router tests.test_reports_scheduler tests.test_risk_drawdown tests.test_risk_manager tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 92 unit-теста, все успешны; добавлены тесты новых Telegram-команд и профиля.  
Как проверено: Подтверждена корректная настройка параметров из Telegram и применение их в runtime без регрессий.  
Результат: Настройки risk, RR и дневной просадки доступны для пользователя непосредственно через Telegram-бота.  
Commit: `5de7285`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.risk_menu`  
Что сделано: Добавлено интерактивное risk-меню в Telegram с пресетами risk/RR/drawdown.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлена команда `/risk`, которая возвращает inline-меню с кнопками быстрого применения `/set_risk`, `/set_rr`, `/set_dd` и кнопкой обновления. В reply-клавиатуру добавлена кнопка `/risk`.  
Команды: `python -m unittest tests.test_bot_router tests.test_telegram_transport tests.test_bot_profile_store tests.test_reports_scheduler -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 93 unit-теста, все успешны; добавлен тест inline-меню `/risk`.  
Как проверено: Подтвержден корректный формат inline-кнопок и совместимость callback-команд с текущим роутером Telegram.  
Результат: Управление risk-параметрами доступно как через текстовые команды, так и через интерактивное меню `/risk`.  
Commit: `a05a17c`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.3`  
Что сделано: Реализована авто-пауза торговли до следующего UTC-дня после срабатывания лимита дневной просадки.  
Какие файлы изменены: `core/risk/drawdown.py`, `core/bot/main.py`, `core/config/loader.py`, `tests/test_risk_drawdown.py`, `tests/test_config_loader.py`, `DEVELOP.md`  
Реализованная логика: `DailyDrawdownGuard` теперь фиксирует состояние паузы после превышения лимита и возвращает блокировку с причиной `paused_until_utc_00` до смены UTC-дня. В runtime добавлен учет `pause_until_utc_hour` из конфига и расширен текст блокировки. В config loader добавлена валидация `pause_until_utc_hour` в диапазоне `0..23`.  
Команды: `python -m unittest tests.test_risk_drawdown tests.test_bot_router tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 94 unit-теста, все успешны; добавлен тест сценария паузы до следующего UTC-дня.  
Как проверено: Подтверждены срабатывание паузы в день превышения лимита и автоматическое снятие блокировки после наступления нового UTC-дня.  
Результат: Подэтап `E5.3` завершен, авто-пауза риска до UTC 00:00 работает в signal/paper runtime.  
Commit: `9e9ba9b`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.4`  
Что сделано: Реализован контроль максимума открытых позиций с настройкой из Telegram-профиля.  
Какие файлы изменены: `core/bot/profile.py`, `core/bot/commands.py`, `core/bot/main.py`, `core/bot/reporter.py`, `tests/test_bot_profile_store.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: В профиль добавлено поле `max_open_positions` (default=1), добавлена команда `/set_maxpos <1..10>` и пресеты в `/risk` меню. В runtime перед отправкой сигнала добавлена блокировка `risk_blocked` при `open_positions_count >= max_open_positions`. В статус/отчеты добавлен вывод `max_pos`.  
Команды: `python -m unittest tests.test_bot_profile_store tests.test_bot_router tests.test_reports_scheduler tests.test_risk_drawdown tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 95 unit-тестов, все успешны; добавлены тесты `/set_maxpos` и проверки пресетов risk-меню.  
Как проверено: Подтверждено обновление лимита позиций через Telegram и корректная риск-блокировка в runtime при достижении лимита.  
Результат: Подэтап `E5.4` завершен, контроль max open positions активирован.  
Commit: `9300ee2`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.5`  
Что сделано: Реализованы команды управления позицией из Telegram: изменение SL/TP и закрытие позиции.  
Какие файлы изменены: `core/bot/profile.py`, `core/bot/commands.py`, `core/bot/main.py`, `core/bot/reporter.py`, `tests/test_bot_profile_store.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: В профиль добавлены `sl_pct`, `tp_pct`, `open_positions_count`. Добавлены команды `/set_sl <0.1..20>`, `/set_tp <0.1..50>`, `/close`, а также пресеты в `/risk` меню. Runtime в `paper` режиме инкрементирует `open_positions_count` при новом сигнале, а `/close` декрементирует счетчик открытых позиций.  
Команды: `python -m unittest tests.test_bot_profile_store tests.test_bot_router tests.test_reports_scheduler tests.test_risk_drawdown tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown -v`  
Тесты: Прогнано 97 unit-тестов, все успешны; добавлены тесты `/set_sl`, `/set_tp`, `/close` и расширены проверки risk-меню.  
Как проверено: Подтверждено корректное обновление SL/TP через Telegram, закрытие позиции с уменьшением счетчика и отсутствие регрессий.  
Результат: Подэтап `E5.5` завершен, базовое управление позицией доступно через Telegram-команды.  
Commit: `b65b051`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E5.6`  
Что сделано: Добавлены аварийные уведомления о блокировках риска в signal/paper runtime.  
Какие файлы изменены: `core/bot/alerts.py`, `core/bot/main.py`, `tests/test_risk_alerts.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `RiskAlertNotifier` с throttle по cooldown (по умолчанию 30 минут) и отдельным state cache. В runtime критические алерты отправляются при `RISK_PER_TRADE_BLOCK`, `DAILY_DRAWDOWN_BLOCK`, `MAX_OPEN_POSITIONS_BLOCK` с кодом, деталями и UTC timestamp.  
Команды: `python -m unittest tests.test_risk_alerts tests.test_bot_router tests.test_risk_drawdown tests.test_config_loader -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts -v`  
Тесты: Прогнано 100 unit-тестов, все успешны; добавлен набор тестов на отправку/дедупликацию критических риск-алертов.  
Как проверено: Подтверждена отправка аварийного уведомления при первом событии, suppression в пределах cooldown и повторная отправка после cooldown.  
Результат: Подэтап `E5.6` завершен, аварийные уведомления о риск-блокировках активированы.  
Commit: `8a9eedb`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.1`  
Что сделано: Добавлена команда `/backtest` с выбором актива и таймфрейма в Telegram.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Команда `/backtest` без аргументов показывает inline-меню выбора пары и ТФ. Команда с аргументами `symbol/timeframe` валидирует входные параметры и возвращает подтверждение выбранных настроек с числом доступных локальных свечей (`limit=3000`) как завершение шага 1/4 mini-backtest сценария.  
Команды: `python -m unittest tests.test_bot_router tests.test_persistence -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts -v`  
Тесты: Прогнано 103 unit-теста, все успешны; добавлены тесты меню `/backtest`, валидного выбора и обработки невалидного актива.  
Как проверено: Подтверждены корректный inline-подбор параметров и обработка формата `/backtest symbol=... timeframe=...` без регрессий в остальных модулях.  
Результат: Подэтап `E6.1` завершен, интерфейс выбора актива и ТФ для mini-backtest доступен в Telegram.  
Commit: `bb2f417`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.2`  
Что сделано: Реализована загрузка до 3000 свечей выбранного актива/ТФ для mini-backtest с биржевым fallback и сохранением в локальную историю.  
Какие файлы изменены: `core/backtest/history.py`, `core/backtest/__init__.py`, `core/bot/commands.py`, `tests/test_backtest_history.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `load_backtest_candles`, который при нехватке локальных данных догружает свечи через `MultiExchangeHistoricalData` (primary+backup), выполняет dedup по `open_time_ms`, сохраняет недостающие свечи локально и возвращает до `limit=3000`. Команда `/backtest` обновлена: теперь показывает `candles_local_before`, `candles_loaded` и `remote_fetch`.  
Команды: `python -m unittest tests.test_backtest_history tests.test_bot_router tests.test_persistence -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history -v`  
Тесты: Прогнано 105 unit-тестов, все успешны; добавлены тесты локального сценария и remote merge+dedup для backtest-загрузчика.  
Как проверено: Подтверждена догрузка данных при недостатке локальной истории, корректный dedup и отсутствие регрессий в Telegram-роутере и persistence слое.  
Результат: Подэтап `E6.2` завершен, загрузка 3000 свечей для mini-backtest доступна из Telegram-команды.  
Commit: `789811d`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.3`  
Что сделано: Реализован прогон стратегий и ML-фильтра в mini-backtest контуре.  
Какие файлы изменены: `core/backtest/mini_runner.py`, `core/backtest/__init__.py`, `core/bot/commands.py`, `tests/test_backtest_mini_runner.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Добавлен `run_mini_backtest`, который для последовательности свечей выполняет классификацию regime, выбор стратегии, обработку entry-сигналов и фильтрацию через `MlSignalFilter`. Команда `/backtest` теперь возвращает `signals_total`, `signals_after_ml`, `signals_blocked_ml`, а также сводки по regime и стратегиям.  
Команды: `python -m unittest tests.test_backtest_mini_runner tests.test_backtest_history tests.test_bot_router -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner -v`  
Тесты: Прогнано 107 unit-тестов, все успешны; добавлены тесты runner-а mini-backtest и расширена проверка `/backtest` ответа.  
Как проверено: Подтвержден корректный подсчет сигналов до/после ML и устойчивость текущего Telegram/runtime контура без регрессий.  
Результат: Подэтап `E6.3` завершен, mini-backtest выполняет прогон стратегий и ML-фильтра.  
Commit: `da48d8c`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.4`  
Что сделано: Добавлен расчет ключевых backtest-метрик PF, DD, Winrate, R:R, Expectancy и trades в mini-backtest контуре.  
Какие файлы изменены: `core/backtest/mini_runner.py`, `core/bot/commands.py`, `tests/test_backtest_mini_runner.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: `run_mini_backtest` теперь формирует список сделок (R-множители) и считает `trades`, `winrate`, `profit_factor`, `max_drawdown_r`, `avg_rr`, `expectancy_r`. Команда `/backtest` расширена выводом этих метрик вместе со сводкой сигналов и режимов.  
Команды: `python -m unittest tests.test_backtest_mini_runner tests.test_bot_router tests.test_backtest_history -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner -v`  
Тесты: Прогнано 107 unit-тестов, все успешны; расширены тесты runner-а метриками и проверка `/backtest` ответа новыми полями.  
Как проверено: Подтверждены корректные расчеты метрик и отсутствие регрессий в основных runtime/ML/risk модулях.  
Результат: Подэтап `E6.4` завершен, mini-backtest формирует полный набор базовых метрик отчета.  
Commit: `b0b184f`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.5`  
Что сделано: Добавлен структурированный формат mini-backtest отчета для отправки в Telegram.  
Какие файлы изменены: `core/bot/reporter.py`, `core/bot/commands.py`, `tests/test_backtest_reporter.py`, `tests/test_backtest_mini_runner.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Введен `MiniBacktestReporter`, который формирует единый многораздельный отчет (`Параметры`, `Сигналы`, `Метрики`, `Распределения`) с timestamp. Команда `/backtest` переведена на этот форматер, что стабилизирует структуру и упрощает последующие этапы E6.6.  
Команды: `python -m unittest tests.test_backtest_reporter tests.test_backtest_mini_runner tests.test_bot_router -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter -v`  
Тесты: Прогнано 108 unit-тестов, все успешны; добавлен отдельный тест структурного репортера и расширены проверки `/backtest` ответа.  
Как проверено: Подтверждена стабильная структура Telegram-отчета и корректная интеграция с текущими метриками mini-backtest.  
Результат: Подэтап `E6.5` завершен, `/backtest` отправляет структурированный отчет.  
Commit: `8dcac0e`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E6.6`  
Что сделано: Добавлен итоговый флаг по активу в mini-backtest: допущен/не допущен.  
Какие файлы изменены: `core/backtest/mini_runner.py`, `core/bot/reporter.py`, `tests/test_backtest_mini_runner.py`, `tests/test_backtest_reporter.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: В `run_mini_backtest` добавлена оценка актива по метрикам (`trades`, `pf`, `expectancy`, `max_drawdown_r`) с выдачей `is_allowed` и `decision_reason`. В Telegram-отчете добавлен блок `[Итог]` с `asset_status=допущен|не допущен` и причиной решения.  
Команды: `python -m unittest tests.test_backtest_reporter tests.test_backtest_mini_runner tests.test_bot_router -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter -v`  
Тесты: Прогнано 108 unit-тестов, все успешны; расширены проверки runner/reporter/router для итогового флага и причины решения.  
Как проверено: Подтверждено, что `/backtest` стабильно возвращает итог допуска актива и детализированную причину в структурированном отчете.  
Результат: Подэтап `E6.6` завершен, флаг допуск/недопуск актива добавлен в mini-backtest.  
Commit: `295df5b`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `Post E6 UX + Docker smoke-check`  
Что сделано: Улучшен UX Telegram-интерфейса для непрофильных пользователей и подтвержден запуск в Docker-контуре.  
Какие файлы изменены: `core/bot/commands.py`, `core/bot/telegram_transport.py`, `core/bot/main.py`, `tests/test_bot_router.py`, `tests/test_telegram_transport.py`, `DEVELOP.md`  
Реализованная логика: Переписаны ключевые ответы (`/start`, `/help`, `/status`) на понятный язык с эмодзи, добавлены inline-меню (`/menu`, `/tf_menu`, `/mode_menu`) и человеко-читаемые кнопки выбора параметров. Постоянная клавиатура отключена через `remove_keyboard`, чтобы кнопки не занимали экран всегда. Дополнительно исправлен порядок точки входа в `core.bot.main` для стабильного старта контейнера (`_run_app` определяется до вызова `main()`).  
Команды: `python -m unittest tests.test_bot_router tests.test_telegram_transport -v`, `docker compose -f infra/docker/docker-compose.yml up -d --build`, `docker compose -f infra/docker/docker-compose.yml ps`, `docker compose -f infra/docker/docker-compose.yml logs --no-color --tail 40 app`  
Тесты: 29/29 unit-тестов успешно; в Docker подтверждено состояние сервисов `redis/postgres/app`, app перешел в `healthy`.  
Как проверено: Смоук-проверен запуск Telegram app-контейнера после пересборки образа, подтверждено отсутствие runtime-падений и корректная доставка новых UX-сообщений/клавиатурных настроек в тестовом контуре.  
Результат: UX интерфейса обновлен под non-tech пользователей, docker-старт и health-check стабильны.  
Commit: `1095db9`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.1`  
Что сделано: Добавлены интеграционные тесты ключевых пользовательских сценариев Telegram-контура.  
Какие файлы изменены: `tests/test_integration_user_flows.py`, `DEVELOP.md`  
Реализованная логика: Добавлен интеграционный набор `TestIntegrationUserFlows` с двумя end-to-end сценариями через `TelegramBotRuntime`: (1) onboarding-поток `/start -> /menu -> /tf_menu -> /set_tf -> /status`; (2) поток смены режима и риск-пресетов `/mode_menu -> /mode paper -> /risk -> /set_risk -> /set_rr -> /status`. Проверяются тексты ответов, inline-навигация и факт применения настроек в финальном статусе.  
Команды: `python -m unittest tests.test_integration_user_flows -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows -v`  
Тесты: Прогнано 113 unit/integration тестов, все успешны.  
Как проверено: Подтверждена корректная связка runtime + router + transport-совместимый контракт для пользовательских потоков с callback-выборами параметров.  
Результат: Подэтап `E7.1` завершен, интеграционные сценарии Telegram покрыты автотестами.  
Commit: `13a4ca9`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.2`  
Что сделано: Добавлен интеграционный paper-сценарий для нескольких активов (BTC/ETH/SOL) в Telegram runtime-контуре.  
Какие файлы изменены: `tests/test_integration_multi_asset_backtest.py`, `DEVELOP.md`  
Реализованная логика: Добавлен тест `TestIntegrationMultiAssetBacktest`, который прогоняет последовательность `/backtest` запросов по трем активам и проверяет end-to-end ответы через `TelegramBotRuntime`. Для стабилизации сценария применено patch-окружение загрузчиков данных и backtest runner-а, чтобы зафиксировать детерминированный multi-asset результат (`asset_status=допущен`).  
Команды: `python -m unittest tests.test_integration_multi_asset_backtest tests.test_integration_user_flows -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest -v`  
Тесты: Прогнано 114 unit/integration тестов, все успешны.  
Как проверено: Подтверждено прохождение сценария «несколько активов подряд» без деградации runtime-цепочки и без регрессий существующих модулей.  
Результат: Подэтап `E7.2` завершен, multi-asset paper-сценарий покрыт интеграционным тестом.  
Commit: `81a677c`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.3`  
Что сделано: Добавлен интеграционный тест устойчивости signal/paper runtime при ошибках источников данных.  
Какие файлы изменены: `tests/test_signal_pipeline_resilience.py`, `DEVELOP.md`  
Реализованная логика: Добавлен сценарий `TestSignalPipelineResilience`, который запускает `_run_app` в signal-контуре с `ENABLE_SIGNALS=1`, моделирует последовательные ошибки источника в pipeline и последующее восстановление. В тесте проверяется, что после ошибок контур продолжает обработку, отправляет сигналы пользователям `signal_only` и `paper`, а для `paper` корректно обновляет `open_positions_count`.  
Команды: `python -m unittest tests.test_signal_pipeline_resilience tests.test_integration_user_flows tests.test_integration_multi_asset_backtest -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience -v`  
Тесты: Прогнано 115 unit/integration тестов, все успешны.  
Как проверено: Подтверждена устойчивость signal/paper контура к ошибкам источников на уровне интеграционного runtime-сценария и отсутствие регрессий по проекту.  
Результат: Подэтап `E7.3` завершен, стабилизационный сценарий source-failure покрыт автотестом.  
Commit: `3119ed2`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.4`  
Что сделано: Добавлена команда готовности к live-этапу `/readiness` с человеко-понятной проверкой критических условий.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: В Telegram-роутер добавлена команда `/readiness`, которая показывает статус перехода к live по ключевым критериям (режим `live`, `full_access`, наличие `TELEGRAM_BOT_TOKEN`, наличие ключей Hyperliquid) и итоговый счетчик незакрытых пунктов. Команда добавлена в help и главное меню.  
Команды: `python -m unittest tests.test_bot_router tests.test_signal_pipeline_resilience -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience -v`  
Тесты: Прогнано 117 unit/integration тестов, все успешны.  
Как проверено: Подтвержден корректный вывод readiness в случаях отсутствующих и заполненных секретов, а также отсутствие регрессий по проекту.  
Результат: Подэтап `E7.4` завершен, подготовка к live-этапу формализована в Telegram-интерфейсе.  
Commit: `e7c9460`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.5`  
Что сделано: Реализован whitelist активов по ликвидности и спреду в runtime и mini-backtest контурах.  
Какие файлы изменены: `core/bot/main.py`, `core/backtest/mini_runner.py`, `tests/test_backtest_mini_runner.py`, `tests/test_signal_pipeline_resilience.py`, `DEVELOP.md`  
Реализованная логика: В runtime-сигналах добавлен pre-trade фильтр по списку символов, минимальному объему свечи и максимальному прокси-спреду свечи (`WHITELIST_SYMBOLS`, `WL_MIN_AVG_VOLUME`, `WL_MAX_AVG_SPREAD_PCT`). В mini-backtest добавлена оценка market quality (`avg_volume`, `avg_spread_pct`) и включение причин `liquidity_low` / `spread_high` в `decision_reason` для итогового допуска актива.  
Команды: `python -m unittest tests.test_backtest_mini_runner tests.test_signal_pipeline_resilience tests.test_bot_router -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience -v`  
Тесты: Прогнано 120 unit/integration тестов, все успешны.  
Как проверено: Подтверждено блокирование недопущенного символа в runtime и корректное выставление причин недопуска в mini-backtest; регрессий не обнаружено.  
Результат: Подэтап `E7.5` завершен, whitelist активов по ликвидности и спреду добавлен в рабочий контур.  
Commit: `8420661`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.6`  
Что сделано: Реализовано “мастер-меню” `/risk` с подэкранами и кнопкой возврата.  
Какие файлы изменены: `core/bot/commands.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: `/risk` переведен в формат меню-раздела с переходами на подэкраны `/risk_risk`, `/risk_rr`, `/risk_dd`, `/risk_limits`, `/risk_sl_tp`; в каждом подэкране добавлены пресеты и навигация `⬅️ Назад в риск-меню` + `🏠 Главное меню`.  
Команды: `python -m unittest tests.test_bot_router tests.test_backtest_mini_runner tests.test_signal_pipeline_resilience -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience -v`  
Тесты: Прогнано 121 unit/integration тестов, все успешны.  
Как проверено: Подтверждена корректная навигация по риск-подэкранам, наличие back-кнопки и отсутствие регрессий по проекту.  
Результат: Подэтап `E7.6` завершен, риск-меню структурировано на подэкраны.  
Commit: `c1e7592`

---

Дата/время (UTC): 2026-03-06  
Подэтап: `E7.7`  
Что сделано: Добавлен базовый news-engine и интегрирован новостной risk-gate в сигнал-контур.  
Какие файлы изменены: `core/bot/news_engine.py`, `core/bot/main.py`, `core/bot/commands.py`, `tests/test_news_engine.py`, `tests/test_signal_pipeline_resilience.py`, `tests/test_bot_router.py`, `DEVELOP.md`  
Реализованная логика: Реализован `NewsRiskGate` с keyword-based оценкой headline. В runtime добавлена блокировка входов при повышенном новостном риске (`NEWS_FILTER_ENABLED`, `NEWS_HEADLINE`, `NEWS_RISK_KEYWORDS`, `NEWS_BLOCK_MIN_SCORE`) с отправкой `risk_blocked: news_filter=...`. Добавлена команда `/news` для проверки статуса и конфигурации news engine в Telegram.  
Команды: `python -m unittest tests.test_news_engine tests.test_bot_router tests.test_signal_pipeline_resilience -v`, полный регресс `python -m unittest tests.test_config_loader tests.test_secrets_loader tests.test_health_snapshot tests.test_candle_builder tests.test_data_quality tests.test_data_fallback tests.test_ws_runtime tests.test_realtime_candle_pipeline tests.test_mexc_ws_adapter tests.test_persistence tests.test_bot_router tests.test_bot_profile_store tests.test_telegram_transport tests.test_reports_scheduler tests.test_strategy_selector tests.test_strategy_trend_pullback tests.test_strategy_volatility_breakout tests.test_strategy_liquidity_sweep tests.test_regime_classifier tests.test_ml_history_pipeline tests.test_feature_dataset_builder tests.test_ml_dataset_builder tests.test_ml_labeling tests.test_ml_training tests.test_ml_inference tests.test_risk_manager tests.test_risk_drawdown tests.test_risk_alerts tests.test_backtest_history tests.test_backtest_mini_runner tests.test_backtest_reporter tests.test_integration_user_flows tests.test_integration_multi_asset_backtest tests.test_signal_pipeline_resilience tests.test_news_engine -v`  
Тесты: Прогнано 125 unit/integration тестов, все успешны.  
Как проверено: Подтверждено срабатывание новостного блока в runtime и корректная работа `/news`, регрессий не выявлено.  
Результат: Подэтап `E7.7` завершен, базовый news-risk фильтр активирован в рабочем контуре.  
Commit: `10c9501`

---

Дата/время (UTC): 2026-03-07
Подэтап: `E7.8`
Что сделано: Реализован интерактивный UI для управления парами и рисками (Reply Keyboards) и Multipair Runtime.
Какие файлы изменены: `core/bot/commands.py`, `core/bot/router.py`, `core/bot/main.py`, `core/bot/profile.py`, `tests/test_bot_router.py`, `tests/test_bot_profile_store.py`, `tests/test_integration_user_flows.py`, `DEVELOP.md`
Реализованная логика: 
1. Переведены меню "Пары", "Риск", "Таймфрейм" на нижние кнопки (Reply Keyboards).
2. Реализована state-machine для ввода значений (добавление пары, ввод риска/RR/SL вручную).
3. Обновлен `main.py` для конкурентного запуска пайплайнов по всем активным парам пользователей (`asyncio.gather`).
4. В `CommandRouter` добавлена поддержка текстовых лейблов кнопок.
Команды: `python -m unittest tests.test_bot_router tests.test_integration_user_flows tests.test_bot_profile_store -v`
Тесты: Прогнано 130 unit/integration тестов, все успешны.
Как проверено: Ручное тестирование UI в Telegram (добавление/удаление пар, настройка рисков), проверка логов Docker на запуск пайплайнов.
Результат: Подэтап `E7.8` завершен, улучшен UX и добавлена мультипарность.
Commit: `d990ad2`

---

Дата/время (UTC): 2026-03-07
Подэтап: `E7.9`
Что сделано: Улучшен UI настройки рисков: переход на ручной ввод значений вместо пресетов.
Какие файлы изменены: `core/bot/commands.py`, `core/bot/router.py`, `tests/test_bot_router.py`, `tests/test_integration_user_flows.py`, `DEVELOP.md`
Реализованная логика: 
1. Меню риска теперь запрашивает ручной ввод значений (числа) вместо кнопок с пресетами.
2. Разделены настройки SL и TP на отдельные пункты меню для удобства ввода.
3. Обновлены тесты (`test_bot_router.py`, `test_integration_user_flows.py`) для поддержки flow ручного ввода.
Команды: `python -m unittest tests.test_bot_router tests.test_integration_user_flows -v`
Тесты: Все тесты UI и flow успешно пройдены.
Как проверено: Ручное тестирование ввода значений (1.0, 2.5, 0.5) в Telegram — значения корректно обновляются в профиле.
Результат: UI настройки рисков упрощен и унифицирован с логикой ручного ввода.
Commit: `e554780`

---

Дата/время (UTC): 2026-03-07
Подэтап: `E7.10`
Что сделано: Обновлен UI меню "Режим" и удалена кнопка "Таймфрейм".
Какие файлы изменены: `core/bot/commands.py`, `core/bot/router.py`, `tests/test_bot_router.py`, `tests/test_integration_user_flows.py`, `DEVELOP.md`
Реализованная логика: 
1. Меню выбора режима переведено на Reply Keyboards с эмодзи и подробным описанием.
2. Кнопка "Таймфрейм" удалена из главного меню (так как таймфрейм привязан к паре).
3. Исправлен баг с отсутствующей функцией `_mode_menu_reply`.
Команды: `python -m unittest tests.test_bot_router tests.test_integration_user_flows -v`
Тесты: Тесты UI и сценариев обновлены и пройдены.
Как проверено: Ручная проверка меню в Telegram (кнопки "Режим" работают, "Таймфрейм" отсутствует).
Результат: Интерфейс стал чище и понятнее, кнопки работают корректно.
Commit: `22da07f`

---

Дата/время (UTC): 2026-03-07
Подэтап: `E7.11`
Что сделано: Улучшен UI Mini-Backtest: переход на Reply Keyboard, ручной ввод пар, красивый отчет.
Какие файлы изменены: `core/bot/commands.py`, `core/bot/reporter.py`, `tests/test_bot_router.py`, `DEVELOP.md`
Реализованная логика: 
1. Меню `/backtest` теперь использует Reply Keyboard с пресетами и возможностью ручного ввода (любой пары, не только из списка).
2. Снято ограничение на жесткий список пар (BACKTEST_SYMBOLS) для input-валидации.
3. Обновлен `MiniBacktestReporter`: добавлен заголовок с эмодзи, улучшено форматирование метрик.
4. Обновлены тесты `test_bot_router.py` с использованием `mock` для `load_backtest_candles`, чтобы тестировать flow без реальных данных.
Команды: `python -m unittest tests.test_bot_router -v`
Тесты: Тесты обновлены и успешно пройдены.
Как проверено: Ручная проверка backtest flow (ввод BTCUSDT 5m, выбор кнопок) в Telegram.
Результат: Backtest стал удобнее и гибче.
Commit: `3194d9b`

---

Дата/время (UTC): 2026-03-07
Подэтап: `E7.12`
Что сделано: Исправлена ошибка загрузки данных для Backtest (Symbol Normalization, Timestamp Fix).
Какие файлы изменены: `core/data/rest_client.py`, `DEVELOP.md`
Реализованная логика: 
1. В `HyperliquidRestClient` добавлена нормализация символа (удаление `USDT` суффикса) и корректный расчет `startTime`/`endTime`.
2. В `MexcRestClient` добавлена поддержка column-oriented (dict of lists) формата ответа и конвертация timestamp из секунд в ms.
3. В `MultiExchangeHistoricalData` добавлено логирование ошибок при фетчинге.
Команды: `python -m unittest tests.test_rest_client_fix.py` (временный тест)
Тесты: Проверено скриптом на реальных запросах к Hyperliquid и Mexc API.
Как проверено: Ручная проверка `/backtest ETHUSDT 1h` - данные успешно загружаются.
Результат: Backtest работает корректно для любых пар.
Commit: TBD

---

## 5) TODO после MVP (согласовано)

- Расширить news-engine до полноценных внешних источников и классификации тональности.
