# Contributor Instructions

## Scope

`yandex-search-cli` is a stateless Python CLI for Yandex web, generative, image, reverse-image, and Wordstat APIs. User setup, credentials, examples, schemas, and full command reference belong in `README.md`, `docs/USAGE.md`, and `llms.txt`.

## Architecture

- `src/yandex_cli/client.py` owns request/response contracts.
- `src/yandex_cli/parsers.py` owns XML parsing.
- CLI entry points parse arguments, call the client, and format output; do not add direct HTTP calls there.
- Preserve command names, exit behavior, and documented JSON schemas unless the task explicitly includes a breaking release.
- Emit machine output to stdout and diagnostics to stderr.
- Never create credential files, modify shell profiles, print keys/folder IDs, or commit secrets.
- Keep commands stateless outside explicitly user-managed credential configuration.

## Verification

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest tests -q
uv build
```

Run affected tests and Ruff for normal changes. Run the full suite and build for packaging, entry-point, parser/client contract, or release changes. Update the relevant README/usage/`llms.txt` surface when public behavior changes.

## Delivery

- Verify locally before pushing; do not use GitHub Actions as the iterative debugger.
- CI should avoid duplicate `push` and PR runs, cancel superseded runs, ignore documentation-only changes, and use bounded timeouts.
- Publishing occurs only from an explicitly approved GitHub release.
