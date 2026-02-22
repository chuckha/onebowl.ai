# OneBowl.ai

Paste a recipe URL, get ingredients organized into prep bowls.

OneBowl uses AI to read a recipe and group ingredients by when they're used during cooking — mise en place made easy.

**Live at [onebowl.ai](https://onebowl.ai).** The app runs on Fly.io with scale-to-zero, so the first load takes at least 1 minute while the machine spins up.

## How it works

1. Submit a recipe URL from any major recipe site
2. The app scrapes the recipe and sends it to an AI provider (Claude or GPT-4)
3. Ingredients are reorganized into labeled bowls based on when they're added
4. Results are cached so the same URL loads instantly next time

## Running locally

```
cp .env.example .env  # fill in your API keys
uv sync
uv run flask run
```

## Stack

Python, Flask, SQLite, Fly.io. AI analysis via Anthropic or OpenAI.
