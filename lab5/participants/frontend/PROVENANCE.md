# Происхождение frontend-материалов (этап 2 пакета)

Входные материалы, приложенные Кожариновым Матвеем к запросу (SHA-256, первые 16 знаков):
```
00e033497f96a1b3…  4e0689dd-____1_______________________________.docx
791822a9c0643356…  ab0fcd44-____2_______________.docx
0650c9f4741d0ab2…  adb1baed-____3_______________.docx
e67029e082aa219a…  e21cc071-__4________________1.docx
```
- ЛР1 (4e0689dd…) побайтно совпадает с reference/lab1_team.docx — повторно не вкладывалась.
- ЛР4 frontend (e21cc071…) побайтно совпадает с reference/lab4_frontend_input.docx — повторно не вкладывалась.
- ЛР2 (ab0fcd44…) и ЛР3 (adb1baed…) — evidence/frontend_lab2.docx и frontend_lab3.docx. По словам Матвея (15.11.2026), все четыре приложенные ЛР — материалы frontend.
- ЛР2: текст и листинг А.1 по содержанию совпадают с ЛР2 ML (reference/lab2_ml.pdf, participants/ml/diagrams/L3_recommendations.puml). Отличаются только пробелы и строка include (в DOCX — сетевой master-URL). Поэтому отдельная .puml не создавалась, чтобы не дублировать L3 ML. Листинг сохранён в originals/lab2_lab3/lab2_recommendations_listingA1.puml.txt (LR2-01).
- ЛР3: L4 TripPlanner (Strategy, 3 стратегии) — диаграмма diagrams/L4_trip_planner.puml (листинг приложения А без изменений, исходное UML-оформление) и код lab3_code/route_optimization.py (листинг приложения Б без изменений). Копии листингов — originals/lab2_lab3/. Расхождения с backend — LR3-01.
- Код web_app/mobile_app и доступ к репозиторию не предоставлены (SRC-01).

| Новый файл (diagrams/) | Основание | Что изменено относительно основания |
|---|---|---|
| L4_trip_planner.puml | Приложение А ЛР3 frontend | Без изменений; рендер штатным UML-движком (Graphviz), как у L4 ML |
| lab3_code/route_optimization.py | Приложение Б ЛР3 frontend | Без изменений; извлечён из DOCX (замена HTML-сущностей и неразрывных пробелов) |
| L1_frontend.puml | Рисунок 2 ЛР1 (originals/lab1_fig2_L1_frontend.png); исходник .puml отсутствовал | Транскрипция изображения; ID по глоссарию ЛР1; добавлены pragma smetana и локальный include |
| L2_frontend.puml | Рисунок 6 ЛР1 (originals/lab1_fig6_L2_frontend.png) | Транскрипция; ID контейнеров по contracts (web→web_app и т.д.); 16 связей как на рисунке |
| L3_web_app.puml | Изображение «Диаграмма компонентов веб-приложения» внутри DOCX ЛР4 (originals/lab4/web_app_components_lab4_docx_image2.png, …image3.svg); в тексте отчёта ЛР4 оно не описано | Транскрипция текста SVG и стрелок PNG; ID web_*_comp назначены заново (proposed); стиль заменён на общую библиотеку C4 |
| L0_frontend.puml | Листинг А.1 ЛР4; исходник подтверждён метаданными PNG отчёта (originals/lab4/L0_frontend.puml.txt) | BUS-01: CRM поддержки и оплата подписки (proposed); порты 443; smetana |
| dynamic_frontend.puml | Листинг А.2 ЛР4 (originals/lab4/dynamic_route_build.puml.txt) | API-01: /api/v1/routes; удалён условный POST /v1/tokens/verify (AUTH-01); добавлены Idempotency-Key, порты 443/8002/8001/5432; C4_Dynamic → C4_Container с номерами в подписях (LIB-01) |
| deployment_frontend.puml | Листинг А.3 ЛР4 (originals/lab4/deployment_frontend.puml.txt) | NET-01: 8443/TLS; HA-01: один edge со статикой, две реплики route_service (proposed); web_spa→web_app; Yandex Cloud → провайдер не утверждён (CLOUD-01) |

Файлы originals/lab4/*.puml.txt извлечены из блока iTXt «plantuml» PNG-рисунков отчёта ЛР4 (PlantUML 1.2024.7). Первая строка «skinparamlocked dpi 220» добавлена генератором при рендере, а не автором. Расширение .txt исключает их из проверки validate.py: они подключают C4_Dynamic.puml, которого нет в общей библиотеке.
