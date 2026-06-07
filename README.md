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

CLI for [Yandex Search API](https://yandex.cloud/en/services/search-api) and YandexGPT — web search and generative AI search from your terminal.

[![PyPI](https://img.shields.io/pypi/v/yandex-search-cli?color=ff6a00&label=PyPI)](https://pypi.org/project/yandex-search-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-ff6a00.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-ff6a00.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/nolan-vale/yandex-search-cli?style=social)](https://github.com/nolan-vale/yandex-search-cli)

</div>

---

## What it does

`yandex-search-cli` wraps the [Yandex Search API](https://yandex.cloud/en/services/search-api) in two terminal commands. It is the practical way to query Yandex — the dominant search engine for Russian-language content — from scripts, pipelines, and AI agent workflows.

`yandex-search` performs web search and returns structured results: title, URL, domain, publication date, and text passages. `yandex-gen` uses YandexGPT to answer a question and cite the sources it used.

Both commands output clean `--json` for use in scripts and AI agents.

## Who it is for

- Developers building automation pipelines over Russian-language web content
- AI agent developers who need structured search output from Yandex
- Researchers working with Russian-language sources, `.ru` domains, or Yandex Cloud
- Anyone using Claude Code, Codex, Cursor, or Windsurf who needs Yandex access from the terminal

## Features

- Web search via Yandex with domain, date, and passage metadata
- Generative search via YandexGPT — answers with cited sources
- Filter results by domain (`--site`)
- Search `.ru`, `.com`, and regional Yandex indexes
- Paginate results (`--page`)
- Filter by region code
- Clean `--json` output for every command

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

# Generative answer with cited sources
yandex-gen "explain the difference between monolith and microservices"

# Restrict generative search to a domain
yandex-gen "how to configure nginx" --site nginx.org

# JSON — extract all URLs
yandex-search "topic" --json | jq -r '.[].url'

# JSON — filter results by domain pattern
yandex-search "regulations" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru"))]'
```

**All flags — `yandex-search`:**

| Flag | Default | Description |
|---|---|---|
| `-n` / `--num-results` | `10` | Number of results |
| `-t` / `--type` | `ru` | Search index: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Region code (e.g. `213` for Moscow) |
| `-p` / `--page` | `0` | Page number, zero-indexed |
| `--site` | — | Restrict results to this domain |
| `--json` | off | JSON array: `[{title, url, domain, date, passages}]` |

**All flags — `yandex-gen`:** `--site`, `--json`

## AI agent usage

`yandex-search-cli` is stateless, read-only, and designed to be called by AI coding assistants (Claude Code, Codex, Cursor, Windsurf, etc.).

```bash
# Search and extract URLs
yandex-search "topic" --json | jq -r '.[].url'

# Collect results across multiple pages
for page in 0 1 2; do
  yandex-search "query" -p $page --json
done | jq -s 'add'

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

See [AGENTS.md](AGENTS.md) for full schemas, exit codes, and environment reference.

→ [Full documentation](docs/USAGE.md)

## Project metadata

- **Author:** Nolan Vale
- **Brand:** Nolan Vale Tools
- **Focus:** search automation, Yandex Search, AI-agent tooling, Russian web workflows, developer productivity
- **License:** MIT

---

Built by [Nolan Vale](https://github.com/nolan-vale)  
Part of **Nolan Vale Tools** — practical open-source utilities for search, automation, AI agents, and developer workflows.
