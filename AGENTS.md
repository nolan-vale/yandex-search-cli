# AGENTS.md — yandex-search-cli for AI Coding Agents

This file is for AI agents (Claude Code, Codex, Cursor, Windsurf, etc.) that need to install and use `yandex-search-cli` on behalf of a user.

## Install & setup

```bash
uv tool install yandex-search-cli
```

**Credentials — Option 1 (config file, recommended):**

```bash
mkdir -p ~/.search-api
echo '{"apiKey": "your-key", "folderId": "your-folder-id"}' > ~/.search-api/config.json
```

**Credentials — Option 2 (environment variables):**

```bash
export YANDEX_API_KEY=your-key
export YANDEX_FOLDER_ID=your-folder-id
```

The user needs a [Yandex Cloud](https://cloud.yandex.ru) account with Search API enabled. Quickstart: https://yandex.cloud/en/docs/search-api/quickstart

## Commands

| Command | What it does |
|---|---|
| `yandex-search <query>` | Web search via Yandex. Returns structured results with domain, date, passages. |
| `yandex-gen <query>` | Generative search via YandexGPT. Returns an AI-written answer with cited sources. |
| `yandex-image-search <query>` | Image search by text query. Returns url, dimensions, format, source page. |
| `yandex-image-search-by-image (--url \| --cbir-id)` | Reverse image search — find pages containing a given image. |
| `yandex-wordstat <top\|dynamics\|regions\|regions-tree>` | Yandex Wordstat query-frequency statistics. |

## Agent Memory v5

- Current task state: `.agent/current.md`.
- Stable repo context: `memory/project.md`.
- Durable decisions: `memory/decisions/*.md`.
- Substantial plans or research syntheses: `memory/specs/*.md`.
- Do not create repo-local task mirrors.

All commands support `--json` for structured output.

## Implementation layout

- `src/yandex_cli/client.py` contains `YandexSearchClient`, the single request/response contract layer.
- `src/yandex_cli/parsers.py` contains XML parsers for base64 `rawData` responses.
- CLI entrypoints in `main.py`, `image_search.py`, and `wordstat.py` should parse args, call `YandexSearchClient`, and format output. Do not put direct `requests.post` calls in entrypoints.

## Recommended agent patterns

```bash
# Web search, structured output
yandex-search "query" --json

# Extract just the URLs
yandex-search "query" --json | jq -r '.[].url'

# Restrict to a specific domain
yandex-search "query" --site habr.com --json

# Generative search (YandexGPT answer with sources)
yandex-gen "question" --json

# Filter results by domain pattern
yandex-search "regulations" --json \
  | jq '[.[] | select(.domain | test("gov\\.ru|edu\\.ru"))]'

# Collect multiple pages
for page in 0 1 2; do
  yandex-search "query" -p $page --json
done | jq -s 'add'

# Search .com Yandex index instead of .ru
yandex-search "machine learning" -t com -n 20 --json

# Image search by text query
yandex-image-search "python logo" --json

# Reverse image search (find pages containing a given image)
yandex-image-search-by-image --url "https://example.com/photo.jpg" --json
yandex-image-search-by-image --cbir-id "abc123..." --page 1 --json

# Wordstat: most popular queries containing a keyword
yandex-wordstat top "python framework" -n 20 --json

# Wordstat: query frequency over time
yandex-wordstat dynamics "python framework" --period monthly --from 2026-01-01 --json

# Wordstat: geographic distribution of a keyword's queries
yandex-wordstat regions "python framework" --scope cities --json

# Wordstat: list of supported region IDs
yandex-wordstat regions-tree --json
```

## JSON output schemas

**yandex-search --json**

```json
[
  {
    "title": "Page title",
    "url": "https://example.ru/page",
    "domain": "example.ru",
    "date": "2024-03-15",
    "passages": ["Relevant text snippet from the page..."]
  }
]
```

**yandex-gen --json**

```json
{
  "message": {
    "content": "YandexGPT answer text...",
    "role": "ROLE_ASSISTANT"
  },
  "sources": [
    {
      "used": true,
      "title": "Source page title",
      "url": "https://..."
    }
  ],
  "isAnswerRejected": false,
  "fixedMisspellQuery": ""
}
```

**yandex-image-search --json**

```json
[
  {
    "url": "https://example.ru/photo.jpg",
    "domain": "example.ru",
    "title": "Page title (often empty — not reliably available from this endpoint)",
    "thumbnail_url": "http://avatars.mds.yandex.net/i?id=...",
    "width": 3000,
    "height": 3000,
    "page_url": "https://example.ru/page",
    "format": "png"
  }
]
```

**yandex-image-search-by-image --json** (raw Search API response, camelCase fields)

```json
{
  "images": [
    {
      "url": "https://example.com/a.jpg",
      "format": "IMAGE_FORMAT_JPEG",
      "width": 800,
      "height": 600,
      "passage": "Text passage near the image",
      "host": "example.com",
      "pageTitle": "Page title",
      "pageUrl": "https://example.com/page"
    }
  ],
  "page": 0,
  "id": "cbir-id-for-pagination"
}
```

**yandex-wordstat top --json**

```json
{
  "totalCount": 4200,
  "results": [{"phrase": "python framework", "count": 1000}],
  "associations": [{"phrase": "python library", "count": 500}]
}
```

**yandex-wordstat dynamics --json**

```json
{"results": [{"date": "2026-01-01T00:00:00Z", "count": 500, "share": 0.0123}]}
```

**yandex-wordstat regions --json**

```json
{"results": [{"region": "213", "count": 300, "share": 0.05, "affinityIndex": 1.42}]}
```

**yandex-wordstat regions-tree --json**

```json
{"regions": [{"id": "225", "label": "Russia", "children": [{"id": "213", "label": "Moscow", "children": []}]}]}
```

## All flags

**yandex-search**

```
yandex-search <query> [-n N] [-t ru|com|tr|kk|be|uz] [-r REGION] [-p PAGE]
              [--site DOMAIN] [--json]
```

**yandex-gen**

```
yandex-gen <query> [--site DOMAIN] [--json]
```

**yandex-image-search**

```
yandex-image-search <query> [-n N] [-t ru|com|tr|kk|be|uz] [-r REGION] [-p PAGE]
                    [--site DOMAIN] [--json]
```

**yandex-image-search-by-image**

```
yandex-image-search-by-image (--url URL | --cbir-id ID) [--site DOMAIN] [-p PAGE]
                              [--family-mode none|moderate|strict] [--json]
```

**yandex-wordstat**

```
yandex-wordstat top <phrase> [-n N] [-r REGION]... [-d all|desktop|phone|tablet]... [--json]
yandex-wordstat dynamics <phrase> --from YYYY-MM-DD [--to YYYY-MM-DD]
                          [--period monthly|weekly|daily] [-r REGION]... [-d DEVICE]... [--json]
yandex-wordstat regions <phrase> [--scope all|cities|regions] [-d DEVICE]... [--json]
yandex-wordstat regions-tree [--json]
```

## Search index types (-t flag)

| Value | Description |
|---|---|
| `ru` | Russian Yandex index (default) |
| `com` | Yandex.com international index |
| `tr` | Turkish index |
| `kk` | Kazakh index |
| `be` | Belarusian index |
| `uz` | Uzbek index |

## Rules for agents

- Keep CLI output stable and script-friendly.
- Do not break JSON output schemas without updating documentation.
- Prefer explicit errors over silent failures.
- Update `README.md`, `docs/USAGE.md`, and `llms.txt` when commands or install instructions change.
- Keep examples copy-pasteable.
- Do not rename terminal commands unless there is a strong reason.

## Properties

- **Stateless** — no local state written between calls
- **Read-only** — never modifies the web or local files
- **Exit codes** — `0` on success, non-zero on error
- **Errors** — specific messages for 401 (bad key), 403 (bad folder/permissions), 429 (rate limit)

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `YANDEX_API_KEY` | if no config file | API key from Yandex Cloud IAM |
| `YANDEX_FOLDER_ID` | if no config file | Folder ID from Yandex Cloud console |

Config file (`~/.search-api/config.json`) takes priority over environment variables.

## Documentation files

- `README.md`: English human-facing overview and quickstart
- `README.ru.md`: Russian overview and examples
- `llms.txt`: compact LLM-facing summary
- `docs/USAGE.md`: detailed command reference
- `CHANGELOG.md`: release notes
