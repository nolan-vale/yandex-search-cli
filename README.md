<div align="center">

[![ru](https://img.shields.io/badge/lang-ru-red.svg)](README.ru.md)

<!--
  COVER IMAGE — generate with this prompt, save as docs/cover.png, then uncomment below.

  Prompt (Midjourney / DALL-E 3 / Stable Diffusion XL):
  "A dark terminal window with glowing Cyrillic search results streaming across the screen,
  Moscow skyline blurred in the background at night, deep navy blue and warm orange gradient,
  minimalist developer tool aesthetic, no UI chrome, no text overlay, professional tech product,
  wide cinematic banner, 2:1 aspect ratio"

  <img src="docs/cover.png" alt="yandex-search" width="100%">
-->

# yandex-search-cli

CLI for [Yandex Search API](https://yandex.cloud/en/services/search-api) and YandexGPT — web search, image search, generative AI search, and Wordstat statistics from your terminal.

[![PyPI](https://img.shields.io/pypi/v/yandex-search-cli?color=ff6a00&label=PyPI)](https://pypi.org/project/yandex-search-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-ff6a00.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-ff6a00.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/nolan-vale/yandex-search-cli?style=social)](https://github.com/nolan-vale/yandex-search-cli)

</div>

---

## What it does

`yandex-search-cli` wraps the [Yandex Search API](https://yandex.cloud/en/services/search-api) in five terminal commands. It is the practical way to query Yandex — the dominant search engine for Russian-language content — from scripts, pipelines, and AI agent workflows.

`yandex-search` performs web search and returns structured results: title, URL, domain, modification date, and text passages. `yandex-gen` uses YandexGPT to answer a question and cite the sources it used. `yandex-image-search` and `yandex-image-search-by-image` search images by text query or by a reference image. `yandex-wordstat` returns query-frequency statistics — top queries, trends over time, and regional distribution.

All commands output clean `--json` for use in scripts and AI agents.

## Who it is for

- Developers building automation pipelines over Russian-language web content
- AI agent developers who need structured search output from Yandex
- Researchers working with Russian-language sources, `.ru` domains, or Yandex Cloud
- Anyone using Claude Code, Codex, Cursor, or Windsurf who needs Yandex access from the terminal

## Features

- Web search via Yandex with domain, date, and passage metadata
- Generative search via YandexGPT — answers with cited sources
- Filter results by domain (`--site`)
- Filter web results by freshness (`--period day|2weeks|month|all`)
- Sort web results by page update time (`--sort time`, optionally `--order asc`)
- Limit generative sources by document format, language and date (`--format pdf --lang en --date '>=20250101'`)
- Continue generative search with a JSON conversation (`--messages-file FILE`, or `-` for stdin)
- Search `.ru`, `.com`, and regional Yandex indexes
- Paginate results (`--page`)
- Filter by region code
- Clean `--json` output for every command
- Image search — find images matching a text query (`yandex-image-search`)
- Reverse image search — find pages containing a given image (`yandex-image-search-by-image`)
- Yandex Wordstat query-frequency statistics — top queries, trends over time, regional distribution (`yandex-wordstat`)

## Installation

```bash
uv tool install yandex-search-cli
```

> No `uv`? Run `curl -LsSf https://astral.sh/uv/install.sh | sh`, or use `pip install yandex-search-cli`.

## Quick start

You need a [Yandex Cloud](https://cloud.yandex.ru) account with Search API enabled ([quickstart](https://yandex.cloud/en/docs/search-api/quickstart)):

```bash
mkdir -p ~/.search-api
echo '{"apiKey": "your-key", "folderId": "your-folder-id"}' > ~/.search-api/config.json
yandex-search "smart city digital platform"
```

> Or via env vars: `export YANDEX_API_KEY=... && export YANDEX_FOLDER_ID=...`

## Usage

```bash
# Web search
yandex-search "smart city digital platform monograph"

# Restrict to a domain
yandex-search "async python" --site habr.com

# Search the .com Yandex index, more results
yandex-search "machine learning" -t com -n 20

# Search the last 24 hours
yandex-search "AI news" --period day --json

# Show recently updated pages first
yandex-search "AI news" --period month --sort time --json

# Generative answer with cited sources
yandex-gen "explain the difference between monolith and microservices"

# Restrict generative search to a domain
yandex-gen "how to configure nginx" --site nginx.org

# Generate an answer from English PDF sources added since January 2025
yandex-gen "smart city research" --format pdf --lang en --date '>=20250101' --json

# Ask a follow-up using earlier user/assistant messages
yandex-gen "How do I enable HTTPS?" --messages-file conversation.json

# JSON — extract all URLs
yandex-search "topic" --json | jq -r '.[].url'

# JSON — filter results by domain pattern
yandex-search "regulations" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru"))]'
```

**All flags — `yandex-search`:**

| Flag | Default | Description |
|---|---|---|
| `-n` / `--num-results` | `10` | Results per page (1–100) |
| `-t` / `--type` | `ru` | Search index: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Region code (e.g. `213` for Moscow) |
| `-p` / `--page` | `0` | Starting page number, zero-indexed |
| `--pages` | `1` | Consecutive pages; deduplicate URLs across pages |
| `--timeout` | `30` | HTTP connect/read timeout in seconds |
| `--version` | — | Show package version without authentication |
| `--site` | — | Restrict results to this domain |
| `--period` | — | Freshness: `all`, `day` (24 hours), `2weeks`, `month` |
| `--sort` | relevance | `relevance` or `time` (page update time, newest first) |
| `--order` | desc | `asc` or `desc`; requires `--sort time` |
| `--json` | off | JSON array: `[{title, url, domain, date, passages}]` |

**All flags — `yandex-gen`:** `--site`, `--format`, `--lang`, `--date`, `--messages-file FILE`, `--json`, `--timeout`, `--version`

Use `--format pdf` to limit source documents to PDF, `--lang en` for an ISO 639-1
language, and `--date '>=20250101'` for a source date filter. Dates also accept an
exact day, an inclusive range (`'20250101..20251231'`), a month (`'202501*'`) or a
year (`'2025*'`). Date filters use Yandex's page-addition date, rather than a
verified publication date. The [usage guide](docs/USAGE.md#yandex-gen) lists all
supported formats and date operators. Filters combine with a site and dialogue.

`--messages-file` reads a UTF-8 JSON array of `{role, content}` messages from a
file, or from stdin when `FILE` is `-`. Roles may be `user`/`assistant` or
`ROLE_USER`/`ROLE_ASSISTANT`. An optional query is appended as a user message;
without a query, the array is the complete request. The CLI does not save or
modify conversation files. See the [dialogue example](docs/USAGE.md#yandex-gen).

**All flags — `yandex-image-search`:** `-n` / `--num-results`, `-t` / `--type`, `-r` / `--region`, `-p` / `--page`, `--site`, `--json`

**All flags — `yandex-image-search-by-image`:** `--url` / `--cbir-id` (one required), `--site`, `--page`, `--family-mode`, `--json`

**All flags — `yandex-wordstat`:** subcommands `top`, `dynamics`, `regions`, `regions-tree` — see [full documentation](docs/USAGE.md) for per-subcommand flags

## AI agent usage

`yandex-search-cli` is stateless, read-only, and designed to be called by AI coding assistants (Claude Code, Codex, Cursor, Windsurf, etc.).

```bash
# Search and extract URLs
yandex-search "topic" --json | jq -r '.[].url'

# Collect results across multiple pages
yandex-search "query" --pages 3 --json

# Generative answer as JSON
yandex-gen "question" --json | jq '.message.content'
```

JSON schema for `yandex-search --json`:
```json
[
  {
    "title": "Page title",
    "url": "https://example.ru/page",
    "domain": "example.ru",
    "date": "2024-03-15",
    "passages": ["Relevant text snippet..."]
  }
]
```

See [the usage guide](docs/USAGE.md) for schemas, exit codes, and environment reference.

→ [Full documentation](docs/USAGE.md)

## How this was built

Spec first, then a plan, then implementation with AI coding agents (Claude Code, Codex). Every diff gets reviewed before merge, and releases go through tests and basic security checks. More on the process on the [Nolan Vale profile](https://github.com/nolan-vale).

## Project metadata

- **Author:** Nolan Vale
- **Brand:** Nolan Vale Tools
- **Focus:** search automation, Yandex Search, AI-agent tooling, Russian web workflows, developer productivity
- **License:** MIT

---

Built by [Nolan Vale](https://github.com/nolan-vale)  
Part of **Nolan Vale Tools** — practical open-source utilities for search, automation, AI agents, and developer workflows.

## Research workflow updates

Use `yandex-search QUERY --pages 3 -n 10 --json` to collect consecutive pages
with duplicate URLs removed. All commands support `--timeout` (default 30 seconds)
and `--version`; Wordstat global flags precede the subcommand. Transient retrieval
failures retry with bounded backoff. XML API errors exit nonzero instead of
appearing as an empty result set; code 15 still means no matches. Web search
regions now use the correct API field. Image search does not support regions.
The `date` field is page modification time, so confirm article publication metadata
at the publisher. Details: [usage guide](docs/USAGE.md).
