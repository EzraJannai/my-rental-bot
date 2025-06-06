# Rental Bot

This repository contains a small Telegram bot that scrapes several Dutch rental websites.

## Requirements

- Python 3.9 or newer

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the following environment variables before running the bot:
   - `TELEGRAM_TOKEN` – Telegram bot token.
   - `TELEGRAM_CHAT_ID` – one or more chat IDs (comma separated) to receive notifications.
   - `CITY` – city to search (e.g. `Apeldoorn`).
   - `PRICE_RANGE` – price range, e.g. `0-1500`.

## Running the bot

Execute:
```bash
python main.py
```

## Running tests

Use `pytest` to run the unit tests:
```bash
pytest
```

## Offline development

Sample HTML and JSON files for each scraper are available in `tests/data/`.
These are snapshots of actual pages from the various rental sites. You can use
them to develop and test the scrapers offline and to experiment with extracting
additional fields.
