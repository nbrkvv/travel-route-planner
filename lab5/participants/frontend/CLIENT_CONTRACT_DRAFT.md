# Черновик клиентского контракта POST /api/v1/routes (frontend → backend)

Статус: **proposed**. Ни код клиента, ни код/OpenAPI backend не предоставлены, поэтому имена полей и типы ниже — проектное предложение для сверки тимлидом. Подтверждено только документами: смысл входа (интересы, бюджет, время/длительность, транспорт, стартовая точка), ответ 201 с маршрутом и предупреждениями, `request_id`, `Idempotency-Key`, коды 401/403/422/503 (ЛР4 backend), реакции клиента на 401/422/таймаут/5xx (ЛР4 frontend, табл. 3.2).

## Запрос
`POST /api/v1/routes` через edge `https://<домен>/api/v1/routes` (443) → route_service :8443/TLS.

Заголовки: `Authorization: Bearer <token>`, `Idempotency-Key: <uuid v4>`, `Content-Type: application/json`.

Тело — имя DTO в отчёте backend: `TripRequest`. Предлагаемые поля (не подтверждены):

| Поле | Тип | Источник смысла |
|---|---|---|
| interests | string[] (ID категорий) | ЛР1, ЛР4 frontend/backend |
| budget | { amount: number, currency: "RUB" } | ЛР1; валюта RUB — из демонстрации ЛР3 backend |
| date | string (ISO 8601) | ЛР1 «даты» |
| time_window | { start: "HH:MM", end: "HH:MM" } или duration_min | ЛР4 frontend «время/длительность» |
| transport | "walk" \| "public" \| "car" | значения перечня не утверждены |
| start | { lat: number, lon: number, source: "geolocation" \| "manual" } | ЛР4 frontend шаг 2 и реакция на отказ геолокации |
| selected_place_ids | string[] (необязательно) | L3 web_app: «выбранные места» |

## Ответ 201 (`RouteDTO` в отчёте backend)
`request_id`, `route_id`, упорядоченные остановки (id, название, координаты, время прибытия/посещения, стоимость), итоговые время, расстояние и стоимость, геометрия пути для карты, `warnings[]` (например, погода недоступна, рекомендации заменены базовой оценкой).

## Ошибки
Предлагается единое тело `{ request_id, code, message, field_errors?: [{field, message}] }`.

| Код | Реакция клиента | Источник |
|---|---|---|
| 401 | повторный вход через IdP и повтор запроса | ЛР4 frontend |
| 403 | сообщение о недостатке прав, без повтора | предложение |
| 422 `validation_error` | ошибки на полях формы, значения сохраняются | ЛР4 frontend |
| 422 `no_feasible_route` | предложить ослабить бюджет или время | ЛР4 frontend + backend (NoFeasibleRoute → 422) |
| 503 / 5xx / таймаут 15 с | сообщение и кнопка повтора с тем же Idempotency-Key | ЛР4 frontend + backend |

Вопрос к backend (ERR-01): оба случая 422 должны различаться полем `code`, иначе клиент не выберет реакцию.
