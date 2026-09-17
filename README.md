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
| `yandex-search` | Web results with titles, URLs, domains, dates, and passages |
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

# Generate an answer with source references
yandex-gen "document review workflow approaches"

# Restrict generative search to a domain
yandex-gen "how to configure nginx" --site nginx.org

# Extract source URLs
yandex-search "topic" --json | jq -r '.[].url'

# Filter structured results by domain pattern
yandex-search "regulations" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru"))]'
```

### Search flags

| Flag | Default | Description |
|---|---|---|
| `-n` / `--num-results` | `10` | Number of results |
| `-t` / `--type` | `ru` | Search index: `ru` · `com` · `tr` · `kk` · `be` · `uz` |
| `-r` / `--region` | — | Provider region code |
| `-p` / `--page` | `0` | Zero-indexed page number |
| `--site` | — | Restrict results to a domain |
| `--json` | off | Structured result array |

Other options:

- **`yandex-gen`:** `--site`, `--json`.
- **`yandex-image-search`:** `-n` / `--num-results`, `-t` / `--type`, `-r` / `--region`, `-p` / `--page`, `--site`, `--json`.
- **`yandex-image-search-by-image`:** `--url` / `--cbir-id` (one required), `--site`, `--page`, `--family-mode`, `--json`.
- **`yandex-wordstat`:** `top`, `dynamics`, `regions`, `regions-tree`; see [full documentation](docs/USAGE.md) for per-command flags and credentials.

## AI-agent workflows

```bash
# Collect URLs
yandex-search "topic" --json | jq -r '.[].url'

# Combine multiple result pages
for page in 0 1 2; do
  yandex-search "query" -p $page --json
done | jq -s 'add'

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

## License

MIT — Nolan Vale. See [LICENSE](LICENSE).
