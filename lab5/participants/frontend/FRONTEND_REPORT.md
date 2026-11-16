# Материалы участника — frontend

**Участник и роль:** Кожаринов Матвей — frontend-разработчик (web_app, mobile_app). Этап подготовлен ИИ-ассистентом по поручению Матвея; Матвей ещё не подтвердил предложенные изменения (см. «Оставшиеся вопросы»).

**Версия входных исходников / коммит:** коммитов нет. Вход — DOCX ЛР1–ЛР4, приложенные Матвеем 15.11.2026 (хэши в PROVENANCE.md). Код клиента и репозиторий не предоставлены.

**Добавленные файлы:**
- diagrams/: L1_frontend, L2_frontend, L3_web_app, L4_trip_planner (ЛР3), L0_frontend, dynamic_frontend, deployment_frontend — .puml + .png + .svg.
- lab3_code/route_optimization.py — прототип ЛР3 без изменений.
- originals/: исходные листинги ЛР4 (извлечены из PNG), изображения ЛР1 рис. 2 и 6, изображение компонентов web_app из DOCX ЛР4.
- evidence/: DOCX ЛР2 и ЛР3 frontend (Матвей подтвердил, что все приложенные ЛР — его материалы).
- CLIENT_CONTRACT_DRAFT.md, PROVENANCE.md, validation/render_log.txt.

Порядок для индивидуального отчёта (локальная перед общей): L1_frontend → общий L1; L2_frontend → общий L2; L3_web_app (и ссылка на L3 сервиса рекомендаций из ЛР2, LR2-01); L4_trip_planner; L0_frontend → общий L0; dynamic_frontend → общая динамика; deployment_frontend → общее развёртывание. Общие схемы готовит тимлид в integrated.

**Изменения контрактов (before → after, причина, источник):**

| ID | Before | After | Причина / источник | Статус |
|---|---|---|---|---|
| API-01 | POST /api/v1/trips | POST /api/v1/routes | отчёт ЛР4 backend, базовый пакет | aligned-draft |
| NET-01 | edge → route_service HTTP/JSON :8000 | HTTPS/TLS :8443 | ЛР4 backend п.4, базовая схема 06 | aligned-draft |
| HA-01 | 2 edge (VRRP) + веб-узлы A/B :8080 | 1 edge Nginx :443 со статикой; 2 реплики route_service | базовая схема 06, ЛР4 backend п.5 | proposed |
| BUS-01 | CRM: профили, согласия, льготы; оплата билетов/экскурсий | CRM поддержки; оплата подписки (проектно) | ЛР4 backend, ЛР4 ML | proposed |
| AUTH-01 | POST /v1/tokens/verify | endpoint не указывается | contracts: auth endpoint не утверждён | proposed |
| LIB-01 | include C4_Dynamic.puml | C4_Container, номера в подписях | C4_Dynamic нет в lab4/vendor | resolved-in-package |
| ID-01 | web_spa, web/mobile/api | web_app, mobile_app, route_service | contracts.containers | proposed |
| CLOUD-01 | Yandex Cloud | провайдер не утверждён | нет в базовых схемах | proposed |

Подтверждённые документами (но не кодом) вызовы клиента — contracts/project.json → frontend_client_calls: getCurrentPosition() с таймаутом 10 с; GET /{z}/{x}/{y} к картам напрямую; POST /api/v1/routes через edge с Bearer и Idempotency-Key, таймаут 15 с; реакции на 401/422/таймаут/5xx. Поля DTO — только черновик (CLIENT_CONTRACT_DRAFT.md).

**Проверки (команда, результат, окружение):** Linux-контейнер, OpenJDK 21.0.12.1, PlantUML 1.2025.2 из lab4/plantuml.jar, Python 3 (/usr/local/bin/python3).
1. `java -jar lab4/plantuml.jar -charset UTF-8 -checkonly participants/frontend/diagrams/*.puml` → exit 0.
2. Рендер `-Sdpi=180 -tpng` и `-tsvg` для шести frontend-схем → exit 0; L4_trip_planner — отдельно (п.4) (validation/render_log.txt).
3. `python validate.py` (без --render, чтобы не перегенерировать изображения ML) → success, 20 самостоятельных диаграмм (13 прежних + 7 frontend), checkonly exit 0, демонстрация ML exit 0. Лог — validation/handoff_checks.json; прежний лог ML — validation/history/package1_ml_handoff_checks.json. Скрипт также проверил в C4-файлах smetana, отсутствие Rel_D/L/R/U, skinparam и сетевых include.
4. ЛР3: checkonly и рендер L4_trip_planner — exit 0; `python3 -I -m py_compile` — exit 0; запуск `route_optimization.py` — exit 0, вывод совпал с разделом 7 ЛР3: InterestFirst → Галерея → Музей, 2100 м, 131 мин, 950 руб.; Shortest → Парк, 800 м, 48 мин, 0 руб.; Balanced → Галерея, 1500 м, 65 мин, 350 руб. (validation/lab3_log.txt). Автотестов в ЛР3 нет.
5. Сверка PACKAGE_SHA256.json входного пакета: 79 файлов, расхождений нет.

**Компиляция и просмотр изображений:** все семь PNG просмотрены визуально: текст читается, связи и подписи соответствуют исходникам. В L2_frontend и dynamic_frontend отдельные линии проходят через подписи и границу системы, но текст остаётся читаемым; раскладку не правил, так как Rel_* и skinparam запрещены. Компиляция не проверяет работу API, TLS и балансировки — это проектная конфигурация. Word на этапе frontend не создавался.

**Реальные ссылки PR/review/CI:** нет. Ветки, коммиты, PR и запуски Actions на этом этапе не создавались. Репозиторий https://github.com/nbrkvv/travel-route-planner из среды обработки открыть не удалось — его содержимое не проверено.

**Оставшиеся вопросы:** SRC-01 (нужен код клиента или ссылка на репозиторий), LR2-01, LR3-01 (нужна ЛР2 с декомпозицией Trip Planning Service, если есть), подтверждение Матвеем HA-01 и BUS-01, AUTH-01, ERR-01, DTO-01 — см. coordination/OPEN_ISSUES.md.

**Следующему участнику требуется:** решить LR2-01/LR3-01 (какой L4 route_service идёт в integrated); сверить API-01/NET-01/DTO-01/ERR-01 с кодом и OpenAPI backend; принять или отклонить HA-01, BUS-01, CLOUD-01, ID-01; свести общие L0/L1/L2/динамику/развёртывание в integrated с учётом frontend-ID; принять PR Матвея с его схемами в репозиторий и провести ревью (Матвей должен открыть PR сам, от своей учётной записи).
