# Current

Updated: 2026-07-27 00:55 +05
Repo: nolan-vale/yandex-search-cli
Branch: main
Active issue: none

## Current
Yandex Search CLI hardening is complete and pushed. Commit `f3f02b8` adds `YandexSearchClient`, moves XML parsing to `parsers.py`, hardens HTTP/JSON/rawData/argparse failures, expands tests to 39 cases, and strengthens CI/publish gates.

## Next
- No active task. For future CLI changes, keep request/response logic in `src/yandex_cli/client.py` and keep entrypoints limited to args, client calls, and output formatting.

## Blockers
- None.

## Checks
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run pytest tests/ -v` (39 passed)
- `uv build`
- Live smoke: `yandex-search`, `yandex-image-search`, and `yandex-wordstat regions-tree` with `jq -e`
- Pushed `f3f02b8` to `origin/main`

## Recovery
Read this file, then `AGENTS.md`, then git status/log.
