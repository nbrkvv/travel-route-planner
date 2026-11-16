# Журнал передачи

## Пакет 1 — ML
Подготовлены исходники и отчёт ML, правила стыковки, референсы и список спорных решений. Командное согласование и удалённая CI не подтверждены. Из документов восстановлены L3, L4 и Python-прототип; переносы строк внутри строковых литералов L3 объединены, сетевое подключение C4 заменено локальным. L1/L2 перенесены из сохранённого комплекта ЛР1 с изменением только пути библиотеки.

## Пакет 2 — frontend
Подготовлено ИИ-ассистентом по поручению Кожаринова Матвея 15.11.2026; Матвей ещё не подтвердил proposed-пункты. Предыдущие материалы сохранены без изменений, кроме coordination/*, contracts/project.json, validation/handoff_checks.json (перезаписан validate.py; прежний — validation/history/package1_ml_handoff_checks.json), PACKAGE_SHA256.json и строки START_HERE.md о текущем этапе.

Добавлено в participants/frontend: шесть локальных схем (L1, L2, L3 web_app, L0, динамика, развёртывание) с PNG/SVG, originals (листинги ЛР4 из метаданных PNG, рисунки ЛР1), evidence (приложенные ЛР2/ЛР3), CLIENT_CONTRACT_DRAFT.md, PROVENANCE.md, FRONTEND_REPORT.md.

Before → after:
- API-01: POST /api/v1/trips → POST /api/v1/routes (frontend-схемы, contracts). Основание — ЛР4 backend. Код не проверен.
- NET-01: edge → route_service HTTP :8000 → HTTPS/TLS :8443.
- HA-01 (proposed): 2 edge + веб-узлы A/B → 1 edge со статикой, 2 реплики route_service.
- BUS-01 (proposed): CRM профилей/льгот и оплата билетов → CRM поддержки и оплата подписки.
- AUTH-01 (proposed): условный POST /v1/tokens/verify удалён из схем.
- LIB-01: C4_Dynamic → C4_Container с номерами в подписях (общая библиотека, стиль не менялся).
- contracts: frontend_alignment, frontend_client_calls, frontend_components, element_aliases, infrastructure_alignment_frontend; status дополнен «frontend_prepared».
- OPEN_ISSUES: статусы API-01, NET-01, HA-01, BUS-01, DTO-01, CI-01 обновлены; добавлены SRC-01, AUTH-01, ERR-01, ID-01, LIB-01, CLOUD-01, DOC-01, VER-01.

Дополнение после уточнения Матвея («все приложенные ЛР — со стороны frontend»): ЛР2/ЛР3 перенесены в evidence как frontend; добавлены L4_trip_planner.puml (листинг А ЛР3 без изменений) с PNG/SVG и lab3_code/route_optimization.py (листинг Б без изменений); DOC-01 заменён на LR2-01 и LR3-01; в contracts добавлены frontend_individual_l4, frontend_lab2 и алиас trip_planning_service → route_service.

Фактически проверено: PlantUML 1.2025.2 checkonly и рендер PNG/SVG семи frontend-схем — exit 0; validate.py без --render — success, 20 диаграмм; демонстрация ML — exit 0; py_compile и запуск прототипа ЛР3 frontend — exit 0, вывод совпал с отчётом; визуальный просмотр шести PNG; сверка хэшей входного пакета — 79/79. Не проверено: код клиента и backend, OpenAPI, GitHub-репозиторий (недоступен из среды), PR, ревью, удалённая CI. Изображения ML не перегенерировались.

## Пакет 3 — тимлид
Заполняет тимлид: решения, общая сборка, реальные PR и CI.

### Фактические проверки пакета 1
13 самостоятельных диаграмм прошли проверку синтаксиса и генерацию PNG/SVG; демонстрация Python ЛР3 завершилась успешно. Это локальная проверка упаковки, не удалённая CI и не ревью коллег. Исторические UML L4 сохранены со своим движком по исходнику; C4 использует Smetana.

## v3 backend_and_lead — 2026-11-16
- До: репозиторий и API не проверены. После: main 0be024f совпадает с GitHub; реализован только доменный планировщик. DTO остаются proposed.
- До: auth/ML в backend-схемах 8443. После: 8002/8001 по предложению общего contracts, сетевых сервисов нет. Затронуты diagrams/lab4 и новые lab5/participants/backend.
- До: разрозненные ID и полные схемы. После: canonical ID в integrated; L2 собирается из трёх include-фрагментов. Старые материалы участников сохранены.
- Самостоятельные L0–L4, динамика, обновление модели, deployment; единая библиотека vendor. L4 сохраняет оформление.
- Исходные DOCX — исторические evidence, не обновлённые отчёты ЛР5.

## Индивидуальное дополнение ML

Дадонов Дмитрий: локальные L0, динамика, развёртывание и сценарий отказа ML перенесены из внешнего каталога lab4 в lab5/participants/ml/diagrams. Пути include адаптированы к общему vendor; существующая CI автоматически обнаруживает эти исходники. Добавлен ML_REPORT.md с локальными схемами перед общими. Код прототипа и общие архитектурные решения не менялись; предложенные контракты/реплики остаются на командном ревью.
