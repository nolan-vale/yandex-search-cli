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
| `--json` | off | JSON-массив: `[{title, url, domain, date, passages}]` |

**Примеры:**

```bash
yandex-search "умный город цифровая платформа"
yandex-search "python async" -n 20
yandex-search "документация" --site docs.djangoproject.com
yandex-search "новости ИИ" -t com
yandex-search "запрос" -p 1 --json
```

---

### yandex-gen

```
yandex-gen <запрос> [параметры]
```

| Флаг | По умолчанию | Описание |
|---|---|---|
| `--site` | — | Ограничить источники доменом |
| `--json` | off | Сырой JSON от Яндекса |

**Примеры:**

```bash
yandex-gen "объясни трансформеры в машинном обучении"
yandex-gen "как настроить nginx reverse proxy" --site nginx.org
yandex-gen "запрос" --json
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
for page in 0 1 2; do
  yandex-search "запрос" -p $page --json
done | jq -s 'add'

# Поиск + сохранение в файл
yandex-search "источники литературы" -n 20 --json > sources.json
```

## Переменные окружения

| Переменная | Обязательно | Описание |
|---|---|---|
| `YANDEX_API_KEY` | если нет файла | API-ключ Yandex Cloud |
| `YANDEX_FOLDER_ID` | если нет файла | ID папки Yandex Cloud |
