<div align="center">

[![en](https://img.shields.io/badge/lang-en-blue.svg)](README.md)

<!--
  <img src="docs/cover.png" alt="yandex-search" width="100%">
-->

# yandex-search-cli

**CLI для [Yandex Search API](https://yandex.cloud/en/services/search-api) — веб-поиск и генеративный поиск YandexGPT из терминала.**

[![PyPI](https://img.shields.io/pypi/v/yandex-search-cli?color=ff6a00&label=PyPI)](https://pypi.org/project/yandex-search-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-ff6a00.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-ff6a00.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/nolan-vale/yandex-search-cli?style=social)](https://github.com/nolan-vale/yandex-search)

</div>

---

`yandex-search` оборачивает [Yandex Search API](https://yandex.cloud/en/services/search-api) в две команды терминала. `yandex-search` — структурированный веб-поиск с доменами, датами и сниппетами. `yandex-gen` — YandexGPT отвечает на вопросы и цитирует источники. Все команды выводят `--json` для скриптов и агентов.

## Запустить за 60 секунд

**Шаг 1 — Установка:**
```bash
uv tool install yandex-search
```

> Нет `uv`? Запусти `curl -LsSf https://astral.sh/uv/install.sh | sh`, или используй `pip install yandex-search-cli`.

**Шаг 2 — Настройка Yandex Cloud:**
1. Зарегистрируйся на [cloud.yandex.ru](https://cloud.yandex.ru)
2. Создай сервисный аккаунт и API-ключ в разделе **IAM**
3. Включи **Yandex Search API** для своего облака ([инструкция](https://yandex.cloud/en/docs/search-api/quickstart))
4. Скопируй **API-ключ** и **Folder ID** из консоли

**Шаг 3 — Укажи credentials:**
```bash
mkdir -p ~/.search-api
echo '{"apiKey": "твой-ключ", "folderId": "твой-folder-id"}' > ~/.search-api/config.json
```

> Можно также через переменные окружения: `export YANDEX_API_KEY=... && export YANDEX_FOLDER_ID=...`

**Шаг 4 — Поиск:**
```bash
yandex-search "умный город цифровая платформа"
```

## Команды

| Команда | Что делает |
|---|---|
| `yandex-search <запрос>` | Веб-поиск: возвращает title, URL, домен, дату, фрагменты текста. |
| `yandex-gen <запрос>` | Генеративный поиск: YandexGPT пишет ответ с цитированием каждого источника. |

Обе команды принимают `--json` — удобно для `jq`, скриптов и AI-агентов.

## Примеры

```bash
# Обычный поиск
yandex-search "умный город цифровая платформа монография"

# Только с конкретного сайта
yandex-search "async python" --site habr.com

# Больше результатов, поиск по .com-индексу
yandex-search "machine learning" -t com -n 20

# Генеративный ответ — YandexGPT с источниками
yandex-gen "в чём разница между монолитом и микросервисами"

# JSON: извлечь все URL
yandex-search "запрос" --json | jq -r '.[].url'

# JSON: только .gov.ru домены
yandex-search "нормативные акты" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru"))]'
```

## Справочник параметров

**`yandex-search`**

| Флаг | По умолчанию | Описание |
|---|---|---|
| `-n` / `--num-results` | `10` | Количество результатов |
| `-t` / `--type` | `ru` | Индекс: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Код региона (например, `213` — Москва) |
| `-p` / `--page` | `0` | Номер страницы (с нуля) |
| `--site` | — | Ограничить поиск доменом |
| `--json` | off | JSON-массив: `[{title, url, domain, date, passages}]` |

**`yandex-gen`**

| Флаг | По умолчанию | Описание |
|---|---|---|
| `--site` | — | Ограничить источники доменом |
| `--json` | off | Сырой JSON от Яндекса |

## Для AI-агентов и скриптов

`yandex-search` создан для вызова из AI-ассистентов (Claude Code, Codex, Cursor и др.). Все команды stateless, read-only, завершаются чисто.

```bash
# Поиск → URL → обработка
yandex-search "монографии по теме" --json | jq -r '.[].url' | head -5

# Сбор результатов с нескольких страниц
for page in 0 1 2; do
  yandex-search "запрос" -p $page --json
done | jq -s 'add'
```

Смотри [AGENTS.md](AGENTS.md) — JSON-схемы, все флаги и паттерны для агентов.

→ **[Полная документация](docs/USAGE.md)**

---

Built by [Nolan Vale](https://github.com/nolan-vale)  
Part of **Nolan Vale Tools** — practical open-source utilities for search, automation, AI agents, and developer workflows.
