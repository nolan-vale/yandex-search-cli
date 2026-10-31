# yandex-search-cli

**A command-line integration for repeatable research using Yandex search, cited answers, image search, and query statistics.**

[Русский](README.ru.md)

[![PyPI](https://img.shields.io/pypi/v/yandex-search-cli?color=334155&label=PyPI)](https://pypi.org/project/yandex-search-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-334155.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-6B705C.svg)](LICENSE)

## Practical purpose

Make recurring research tasks reusable: gather web sources, obtain cited answers, retrieve image-search results, and inspect query-frequency data through structured command-line output. The tool is useful for workflows involving Russian-language or regional sources as well as other supported search indexes.

Yandex supplies the underlying search, generative answers, and statistics. This repository connects those services to scripts and AI agents; it is not a separately developed search engine or AI model.

## Project contribution

Built with AI coding agents as part of [Nolan Vale's](https://github.com/nolan-vale) independent product and workflow-automation work. My contribution is defining the task and interface, directing AI-assisted implementation, checking results, and iterating. **Nolan Vale Tools** is the label for these independent public projects.

## What it does

| Command | Purpose |
|---|---|
| `yandex-search` | Web results with titles, URLs, domains, modification dates, and passages |
| `yandex-gen` | A generated answer with source references through YandexGPT |
| `yandex-image-search` | Image search by text |
| `yandex-image-search-by-image` | Image search by reference image |
| `yandex-wordstat` | Query-frequency statistics, trends, and regional distribution |

Commands support `--json` for scripts and AI-agent workflows. Available data, filters, and access requirements depend on the relevant Yandex service.

## Installation

```bash
uv tool install yandex-search-cli
```

Alternatively, use `pip install yandex-search-cli` in a suitable Python environment.

## Quick start

For web search, configure a Yandex Cloud account with Search API access. Keep credentials out of source control:

```bash
export YANDEX_API_KEY=your-key
export YANDEX_FOLDER_ID=your-folder-id
yandex-search "document review workflow" --json
```

The tool also supports a configuration file at `~/.search-api/config.json` with `apiKey` and `folderId` fields. Treat this as a credential file, not project documentation. Other service-specific setup is described in [full usage documentation](docs/USAGE.md).

## Usage

```bash
# Web search
yandex-search "smart city digital platform monograph"

# Restrict to a domain
yandex-search "async python" --site habr.com

# Choose an index and request more results
yandex-search "machine learning" -t com -n 20

# Recent results, sorted by page update time
yandex-search "AI news" --period month --sort time --json

# Generate an answer with source references
yandex-gen "document review workflow approaches"

# Restrict generative search to a domain
yandex-gen "how to configure nginx" --site nginx.org

# Limit sources by format, language and date
yandex-gen "smart city research" --format pdf --lang en --date ">=20250101" --json

# Continue a conversation from earlier user/assistant messages
yandex-gen "How do I enable HTTPS?" --messages-file conversation.json

# Extract source URLs
yandex-search "topic" --json | jq -r '.[].url'

# Filter structured results by domain pattern
yandex-search "regulations" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru"))]'
```

### Search flags

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

## AI-agent workflows

```bash
# Collect URLs
yandex-search "topic" --json | jq -r '.[].url'

# Combine multiple result pages
yandex-search "query" --pages 3 --json

# Retrieve an answer as JSON
yandex-gen "question" --json | jq '.message.content'
```

Example search output:

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

See [AGENTS.md](AGENTS.md) and [full usage documentation](docs/USAGE.md) for integration details. Use the installed commands' `--help` when checking supported options.

## Scope and review

This tool sends queries and other request inputs to external Yandex services. It is not an offline research system. Protect credentials, use only material you are authorized to submit, and review source references and generated answers before using them in decisions or external communications.

The repository demonstrates AI-assisted integration and workflow design. Provider availability, source quality, and the suitability of results for a particular task require separate evaluation.

## Research workflow updates

Use `yandex-search QUERY --pages 3 -n 10 --json` to collect consecutive pages
with duplicate URLs removed. All commands support `--timeout` (default 30 seconds)
and `--version`; Wordstat global flags precede the subcommand. Transient retrieval
failures retry with bounded backoff. XML API errors exit nonzero instead of
appearing as an empty result set; code 15 still means no matches. Web search
regions now use the correct API field. Image search does not support regions.
The `date` field is page modification time, so confirm article publication metadata
at the publisher. Details: [usage guide](docs/USAGE.md).

## License

MIT — Nolan Vale. See [LICENSE](LICENSE).
