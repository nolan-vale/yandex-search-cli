# yandex-search-cli — Полная документация

← [Назад в README](../README.md)

## Установка

```bash
uv tool install yandex-search-cli   # рекомендуется
pip install yandex-search-cli       # или pip
```

## Настройка

**Вариант 1: файл конфигурации (рекомендуется)**

```bash
mkdir -p ~/.search-api
cat > ~/.search-api/config.json << 'EOF'
{
  "apiKey": "ваш-api-ключ",
  "folderId": "ваш-folder-id"
}
EOF
```

**Вариант 2: переменные окружения**

```bash
export YANDEX_API_KEY=ваш-api-ключ
export YANDEX_FOLDER_ID=ваш-folder-id
```

Оба варианта работают одинаково. Файл конфигурации имеет приоритет, если он существует.

[Как получить API-ключ и folder ID →](https://yandex.cloud/en/docs/search-api/quickstart)

---

## Команды

### yandex-search

```
yandex-search <запрос> [параметры]
```

| Флаг | По умолчанию | Описание |
|---|---|---|
| `-n` / `--num-results` | `10` | Количество результатов |
| `-t` / `--type` | `ru` | Индекс поиска: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Код региона (например, `213` — Москва) |
| `-p` / `--page` | `0` | Номер страницы (с 0) |
| `--site` | — | Ограничить поиск доменом |
| `--period` | — | Свежесть: `all`, `day` (24 часа), `2weeks`, `month` |
| `--sort` | relevance | `relevance` или `time` — по времени обновления страниц |
| `--order` | desc | `asc` — сначала старые; `desc` — сначала новые; требуется `--sort time` |
| `--json` | off | JSON-массив: `[{title, url, domain, date, passages}]` |

**Примеры:**

```bash
yandex-search "умный город цифровая платформа"
yandex-search "python async" -n 20
yandex-search "документация" --site docs.djangoproject.com
yandex-search "новости ИИ" -t com
yandex-search "новости ИИ" --period day --pages 2 --json
yandex-search "новости ИИ" --sort time --pages 2 --json
yandex-search "новости ИИ" --period month --sort time --order asc --json
yandex-search "запрос" -p 1 --json
```

`--period` передаёт фильтр свежести в Yandex Search API: `all` — за всё время,
`day` — за последние 24 часа, `2weeks` — за последние две недели, `month` — за
последний месяц. Без флага сохраняется обычный поиск без ограничения периода.
Фильтр действует на все запрошенные страницы и сочетается с `--site`, `--type`
и `--region`. Поле `date` в результате по-прежнему содержит дату изменения
страницы, а не подтверждённую дату публикации.

`--sort time` включает сортировку на стороне API по времени обновления страницы:
по умолчанию сначала новые (`desc`), с `--order asc` — сначала старые.
`--sort relevance` явно выбирает обычную сортировку по релевантности. Без
`--sort` и `--order` настройки сортировки не отправляются, сохраняется обычное
поведение API. `--order` без `--sort time` возвращает ошибку аргументов.
Настройки сортировки и периода сохраняются на всех страницах `--pages`.

---

### yandex-gen

```
yandex-gen [<запрос>] [параметры]
```

| Флаг | По умолчанию | Описание |
|---|---|---|
| `--site` | — | Ограничить источники доменом |
| `--format` | — | Формат документа-источника: `pdf`, `xls`, `ods`, `rtf`, `ppt`, `odp`, `swf`, `odt`, `odg`, `doc` |
| `--lang` | — | Двухбуквенный код языка ISO 639-1: например, `ru` или `en` |
| `--date` | — | Дата добавления источника в поиск в синтаксисе Яндекса |
| `--messages-file FILE` | — | История диалога в UTF-8 JSON; `-` читает stdin |
| `--json` | off | JSON-ответ YandexGPT |

**Примеры:**

```bash
yandex-gen "объясни трансформеры в машинном обучении"
yandex-gen "как настроить nginx reverse proxy" --site nginx.org
yandex-gen "исследования умных городов" --format pdf --lang ru --date '>=20250101' --json
yandex-gen "запрос" --json
```

Фильтры можно задавать отдельно или вместе; они также сочетаются с `--site` и
`--messages-file`. Формат и код языка принимаются без учёта регистра (`PDF`,
`RU` приводятся к `pdf`, `ru`). В запрос API передаётся массив `searchFilters`,
по одному объекту на формат, язык и дату; без фильтров это поле отсутствует.
Формат относится к документам-источникам, а `--json` по-прежнему управляет
выводом команды.

Поддерживаемые значения `--date`:

| Значение | Значение фильтра |
|---|---|
| `'20250101'` | Точный день |
| `'>20250101'`, `'>=20250101'` | После указанного дня или начиная с него |
| `'<20250101'`, `'<=20250101'` | До указанного дня или по него включительно |
| `'20250101..20251231'` | Включительный диапазон |
| `'202501*'` | Месяц |
| `'2025*'` | Год |

Даты должны существовать в календаре, начало диапазона не может быть позже
конца. Ошибки формата документа, кода языка, календарной даты и диапазона дают
exit code 2 до чтения credentials и обращения к API. Значения с `<`, `>` или `*`
заключай в кавычки, чтобы shell не обработал их как перенаправление или glob.
По [документации Яндекса](https://yandex.ru/support/search/ru/query-language/search-operators)
фильтр относится к дате добавления страницы в поиск, а не к подтверждённой
дате публикации статьи.

Для диалога передай предыдущие сообщения массивом JSON. Например,
`conversation.json`:

```json
[
  {"role": "user", "content": "What is Yandex Search API?"},
  {"role": "assistant", "content": "A service for searching the web with Yandex."}
]
```

```bash
# Добавить новый вопрос к истории.
yandex-gen "How do I connect it to MCP?" --messages-file conversation.json --site yandex.cloud --json

# То же самое, прочитав историю из stdin.
yandex-gen "How do I connect it to MCP?" --messages-file - --json < conversation.json
```

Новый запрос добавляется после истории с ролью `ROLE_USER`. Если массив уже
содержит последний вопрос пользователя, запрос можно опустить:
`yandex-gen --messages-file conversation.json --json`.
Допустимы роли `user`, `assistant`, `ROLE_USER`, `ROLE_ASSISTANT`; первые две
приводятся к именам ролей API. Весь запрос, включая добавленный вопрос, должен
содержать 1–100 сообщений; каждое `content` — непустую строку длиной не более
16384 символов. Ошибки файла, JSON, ролей и лимитов дают exit code 2 до чтения
credentials и сетевого запроса, без вывода текста сообщений в диагностике.

CLI только читает историю и не сохраняет диалог автоматически. Для следующего
шага передай обновлённую историю, включающую предыдущий вопрос и ответ из поля
`message` результата. `--json` сохраняет прежний формат ответа API, без новой
обёртки. Контракты фильтров, сортировки и сообщений проверены по официальным схемам
[WebSearchRequest](https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/search_service.proto)
и [GenSearchRequest](https://github.com/yandex-cloud/cloudapi/blob/master/yandex/cloud/searchapi/v2/gen_search_service.proto).

---

### yandex-image-search

```
yandex-image-search <запрос> [параметры]
```

| Флаг | По умолчанию | Описание |
|---|---|---|
| `-n` / `--num-results` | `10` | Количество результатов |
| `-t` / `--type` | `ru` | Индекс поиска: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Не поддерживается image API; возвращает ошибку |
| `-p` / `--page` | `0` | Номер страницы (с 0) |
| `--site` | — | Ограничить поиск доменом |
| `--json` | off | JSON-массив: `[{url, domain, title, thumbnail_url, width, height, page_url, format}]` |

**Примеры:**

```bash
yandex-image-search "python logo"
yandex-image-search "python logo" -n 20
yandex-image-search "sunset" --site unsplash.com
yandex-image-search "sunset" --json
```

---

### yandex-image-search-by-image

```
yandex-image-search-by-image (--url URL | --cbir-id ID) [параметры]
```

| Флаг | По умолчанию | Описание |
|---|---|---|
| `--url` | — | URL картинки для поиска (взаимоисключающе с `--cbir-id`) |
| `--cbir-id` | — | CBIR ID из поля `id` предыдущего ответа |
| `--site` | — | Ограничить результаты доменом |
| `-p` / `--page` | `0` | Номер страницы (с 0) |
| `--family-mode` | — | Фильтрация контента: `none` · `moderate` · `strict` |
| `--json` | off | JSON-ответ Yandex Search API |

**Примеры:**

```bash
yandex-image-search-by-image --url "https://example.com/photo.jpg"
yandex-image-search-by-image --url "https://example.com/photo.jpg" --site habr.com
yandex-image-search-by-image --cbir-id "abc123..." --page 1
```

---

### yandex-wordstat

```
yandex-wordstat <top|dynamics|regions|regions-tree> [параметры]
```

| Подкоманда | Описание |
|---|---|
| `top <фраза>` | Самые частые запросы, содержащие ключевое слово (`-n`, `--device`, `--region`) |
| `dynamics <фраза> --from ДАТА` | Частота запросов во времени (`--period monthly\|weekly\|daily`, `--to`) |
| `regions <фраза>` | География запросов (`--scope all\|cities\|regions`) |
| `regions-tree` | Список поддерживаемых регионов и их ID |

**Примеры:**

```bash
yandex-wordstat top "python framework" -n 20
yandex-wordstat dynamics "python framework" --period monthly --from 2026-01-01
yandex-wordstat regions "python framework" --scope cities
yandex-wordstat regions-tree
```

---

## Формат JSON (yandex-search)

```json
[
  {
    "title": "Заголовок страницы",
    "url": "https://example.ru/page",
    "domain": "example.ru",
    "date": "2024-03-15",
    "passages": ["Релевантный фрагмент текста из страницы..."]
  }
]
```

---

## Скрипты и пайплайны

```bash
# Извлечь все URL
yandex-search "монографии умный город" --json | jq -r '.[].url'

# Только .gov.ru и .edu.ru домены
yandex-search "нормативные акты" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru|edu\\.ru"))]'

# Сбор нескольких страниц
yandex-search "запрос" --pages 3 --json

# Поиск + сохранение в файл
yandex-search "источники литературы" -n 20 --json > sources.json
```

## Переменные окружения

| Переменная | Обязательно | Описание |
|---|---|---|
| `YANDEX_API_KEY` | если нет файла | API-ключ Yandex Cloud |
| `YANDEX_FOLDER_ID` | если нет файла | ID папки Yandex Cloud |

## Сбор научных источников и надёжность (0.2.3)

```bash
# Три последовательные страницы с удалением повторов URL.
yandex-search "искусственный интеллект государственные закупки" --site cyberleninka.ru -n 10 --pages 3 --json

# Регион влияет на ранжирование; поддерживается web search с типом ru/tr.
yandex-search "цифровизация государственных закупок" --region 54 --timeout 45 --json

yandex-search --version
yandex-wordstat --timeout 45 top "государственные закупки" --json
```

`--pages` задаёт количество последовательных страниц начиная с `--page`.
`-n` задаёт число результатов на страницу (1–100). Клиент сохраняет порядок
выдачи, убирает точные повторы непустых URL при сборе нескольких страниц и
останавливается на пустой странице. Доступно не более 250 результатов по одному
запросу; недоступные страницы отсекаются до обращения к API. Если одна из страниц
завершилась ошибкой, команда возвращает ошибку вместо неполного JSON с видом
успешного результата. JSON остаётся массивом `[{title, url, domain, date, passages}]`.

Все команды поддерживают `--timeout SECONDS` (по умолчанию 30 секунд, конечное
положительное число) и `--version`. Для `yandex-wordstat` общие flags указываются
перед подкомандой. Timeout ограничивает подключение и ожидание данных каждого
HTTP-запроса, а не суммарное время сбора страниц. Для поиска, картинок и Wordstat
временные сетевые сбои, HTTP 429/500/502/503/504 повторяются до трёх попыток с
backoff 1/2 секунды; `Retry-After` учитывается с пределом ожидания 30 секунд.
Generative search автоматически не повторяется. Ошибки авторизации не повторяются.

XML `<error>` больше не превращается в успешную пустую выдачу: код 15 означает
отсутствие результатов, остальные коды дают ненулевой exit code. Диагностика
попадает в stderr, API keys и folder IDs скрываются. Ошибки аргументов дают exit
code 2 до чтения credentials и сетевых запросов. Запрос вместе с `--site` должен
содержать не более 400 символов и не может быть пустым.

Web search передаёт `region` на верхнем уровне API-запроса. Image search не
поддерживает регион: сохранённый для совместимости flag `--region` возвращает
понятную ошибку вместо отправки неподдерживаемого поля. Поле `date` — дата
изменения страницы из XML `modtime`, а не подтверждённая дата публикации статьи.
Некорректная дата остаётся пустой. DOI, авторов и год статьи проверяй у издателя
или в репозитории; CLI находит ссылки и snippets, оригинальные PDF скачиваются
отдельно.

Контракт проверен 2026-10-28 по официальным источникам:
[WebSearch](https://yandex.cloud/en/docs/search-api/api-ref/WebSearch/search),
[ImageSearch](https://yandex.cloud/en/docs/search-api/api-ref/ImageSearch/search),
[XML errors](https://yandex.cloud/en/docs/search-api/reference/error-codes),
[лимит выдачи](https://yandex.cloud/en/docs/search-api/concepts/web-search).
