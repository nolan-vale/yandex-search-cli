# yandex-search-cli

**Командная интеграция для повторяемых исследований: поиск Яндекса, ответы с источниками, поиск изображений и статистика запросов.**

[English](README.md)

[![PyPI](https://img.shields.io/pypi/v/yandex-search-cli?color=334155&label=PyPI)](https://pypi.org/project/yandex-search-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-334155.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-6B705C.svg)](LICENSE)

## Назначение и вклад

Инструмент связывает существующие сервисы Яндекса со скриптами и AI-агентами: позволяет собирать источники, получать ответы со ссылками и использовать структурированные результаты в дальнейшей работе. Поиск, генерацию и статистику предоставляет Яндекс; этот репозиторий — интеграция, а не собственная поисковая система или AI-модель.

Проект создан с coding-агентами в рамках независимой практики [Nolan Vale](https://github.com/nolan-vale). Мой вклад: постановка задачи, требования к интерфейсу, направление реализации с AI, проверка результата и итерации. **Nolan Vale Tools** — название независимых публичных проектов.

## Установка и настройка

```bash
uv tool install yandex-search-cli
export YANDEX_API_KEY=your-key
export YANDEX_FOLDER_ID=your-folder-id
yandex-search "обработка документов рабочий процесс" --json
```

Можно использовать `pip install yandex-search-cli` в подходящем Python-окружении. Для Search API нужен соответствующий доступ в Yandex Cloud. Также поддерживается файл `~/.search-api/config.json` с полями `apiKey` и `folderId`. Это файл с секретными данными: не помещайте его в репозиторий.

У отдельных сервисов могут отличаться требования к авторизации. Настройки, в том числе для Wordstat, описаны в [полной документации](docs/USAGE.md).

## Команды

| Команда | Назначение |
|---|---|
| `yandex-search <query>` | Веб-результаты: заголовки, URL, домены, даты и фрагменты |
| `yandex-gen <query>` | Генеративный ответ YandexGPT со ссылками на источники |
| `yandex-image-search <query>` | Поиск изображений по тексту |
| `yandex-image-search-by-image` | Поиск по изображению: URL или CBIR ID |
| `yandex-wordstat <top\|dynamics\|regions\|regions-tree>` | Статистика частотности запросов, динамика и региональные данные |

Команды поддерживают `--json` для скриптов и AI-агентов.

## Примеры

```bash
# Поиск с ограничением по домену
yandex-search "async python" --site habr.com

# Индекс и количество результатов
yandex-search "machine learning" -t com -n 20

# Ответ со ссылками на источники
yandex-gen "подходы к автоматизации обработки документов"

# Получить URL из структурированного вывода
yandex-search "запрос" --json | jq -r '.[].url'

# Поиск изображений
yandex-image-search "python logo"
yandex-image-search-by-image --url "https://example.com/photo.jpg"

# Статистика запросов
yandex-wordstat top "python framework" -n 20
yandex-wordstat dynamics "python framework" --period monthly --from 2026-01-01
yandex-wordstat regions "python framework" --scope cities
```

## Параметры

| Флаг `yandex-search` | По умолчанию | Назначение |
|---|---|---|
| `-n` / `--num-results` | `10` | Количество результатов |
| `-t` / `--type` | `ru` | Индекс: `ru`, `com`, `tr`, `kk`, `be`, `uz` |
| `-r` / `--region` | — | Код региона провайдера |
| `-p` / `--page` | `0` | Номер страницы с нуля |
| `--site` | — | Ограничение доменом |
| `--json` | off | Структурированный JSON-вывод |

`yandex-gen` поддерживает `--site` и `--json`. Для обратного поиска доступны `--url` или `--cbir-id`, а также `--site`, `--page`, `--family-mode` и `--json`. Параметры остальных команд проверяйте в `--help` и [docs/USAGE.md](docs/USAGE.md).

## Работа со скриптами

```bash
for page in 0 1 2; do
  yandex-search "запрос" -p $page --json
done | jq -s 'add'
```

[AGENTS.md](AGENTS.md) содержит дополнительные инструкции по интеграции.

## Данные и проверка результатов

Запросы и другие входные данные передаются внешним сервисам. Это не локальная поисковая система. Защищайте ключи, отправляйте только разрешённые материалы и проверяйте источники и сгенерированные ответы перед использованием в решениях или внешней переписке.

Доступность функций зависит от соответствующего сервиса Яндекса. Интеграция не гарантирует качество источников или пригодность результата для конкретной задачи.

[Полная документация](docs/USAGE.md) · [Английский обзор](README.md).

MIT — Nolan Vale. См. [LICENSE](LICENSE).
