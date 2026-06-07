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

Both commands support `--json` for structured output.

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
