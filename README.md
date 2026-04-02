## What This Is

A Telegram bot that recommends wines by combining data from two sources:
- **Barbora** (Lithuanian grocery retailer) — price, availability, product images
- **Vivino** (wine rating platform) — ratings, grape varieties, alcohol content

Pre-scraped and matched data lives in `data/red_wines.json`, `data/white_wines.json`, `data/rose_wines.json`.

## Project Structure

```
winebot/
├── src/
│   └── lambda_function.py   # AWS Lambda webhook handler
├── data/
│   ├── red_wines.json
│   ├── white_wines.json
│   └── rose_wines.json
└── requirements.txt
```

## Deployment

The bot runs on AWS Lambda triggered by Telegram webhooks via API Gateway.

Set `TELEGRAM_TOKEN` as a Lambda environment variable.

Wine data is loaded from S3 bucket `winebot`.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Architecture

**Data flow:**
1. Telegram sends a webhook POST to API Gateway → Lambda
2. `lambda_handler` parses the message: `[wine_type] [count]` (e.g., `white 5`)
3. Valid wine types: `red`, `white`, `rose` (case-insensitive). Limit: 20 wines max.
4. Loads matching JSON from S3, filters inactive Barbora listings, sorts by Vivino rating descending
5. Sends one `sendPhoto` per wine via Telegram API with HTML caption (title, price, rating, verified flag, Vivino image links)

**Data model:**
- `BarboraVivinoWine` — top-level: `barbora_wine`, `vivino_wines[]`, `verified` flag
- `BarboraWine` — retailer data (price, image URL, availability status)
- `VivinoWine` — rating data (rate, grapes, alcohol, image)

`verified` flag indicates a manually confirmed Barbora↔Vivino match. Each wine can have multiple Vivino matches; only the first match's rating is used for sorting.
