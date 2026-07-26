# yandex-search-cli

## Current State

CLI wrapper for Yandex Search API, generative search, image search, reverse image search, and Wordstat.

## Stable Context

- Never print or commit Yandex credentials.
- Use structured JSON output for agent processing.
- Use for Russian/RuNet research when the repository policy calls for it.
- `src/yandex_cli/client.py` is the request/response contract layer via `YandexSearchClient`.
- `src/yandex_cli/parsers.py` owns web/image XML parsing for base64 `rawData`.
- CLI entrypoints should parse args, call `YandexSearchClient`, and format output; do not add direct `requests.post` calls there.

## Next Actions

- No active memory task.

## Links

- Commands: `yandex-search`, `yandex-gen`, `yandex-image-search`, `yandex-wordstat`
