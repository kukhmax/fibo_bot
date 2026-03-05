# DEVELOP.md — Детализация этапов и журнал реализации

## 1) Правила работы по подэтапам

- Работа ведется подэтапами с уникальным ID: `E<этап>.<подэтап>`.
- После завершения каждого подэтапа фиксируется запись в разделе `Журнал выполнения`.
- После записи в журнал все изменения добавляются в git и создается подробный коммит.
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
Commit: будет добавлен после фиксации изменений в git.

---

## 5) TODO после MVP (согласовано)

- Добавить whitelist активов по ликвидности и спреду.
- Добавить полноценный news-engine (временный ориентир: t.me/cryptoarsenal).
