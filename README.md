# eBay Sold Items Scraper

A web scraper built with Scrapy to extract sold items data from eBay UK. Features rotating Tor proxies, anti-bot measures, and SQLite storage.

## First Time Installation & Set Up

1. Clone the repository:
```bash
git clone <repository-url>
cd ebay-scraper
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up Tor proxies:
```bash
cd tor_proxy
python3 tor_proxy_setup.py
docker compose up -d
```

## Configuration

### Spider Settings
The main settings can be found in `ebay_scraper/settings.py`:

- `CONCURRENT_REQUESTS`: Maximum concurrent requests (default: 16)
- `AUTOTHROTTLE_ENABLED`: Enable/disable automatic throttling
- `AUTOTHROTTLE_START_DELAY`: Initial download delay
- `AUTOTHROTTLE_MAX_DELAY`: Maximum download delay
- `ROTATING_PROXY_LIST_PATH`: Path to proxy list
- `ROTATING_PROXY_PAGE_RETRY_TIMES`: Number of retries per proxy

## Usage

### Required Search Query
The `search_query` argument is **required** when running the spider. You must provide it using the `-a` flag, and the value must be wrapped in quotes. For example:
```bash
scrapy crawl ebay_sold_items -a search_query="size 9 nikes"
```

If the `search_query` argument is not provided, the spider will raise an error and stop execution.

### Limit Number of Items
You can optionally specify the maximum number of items to scrape using the `max_items` argument:
```bash
scrapy crawl ebay_sold_items -a search_query="size 9 nikes" -a max_items=100
```

### Output Formats
You can optionally save results to CSV or JSON. It is recommended to use this with the `max_items` argument:
```bash
# JSON format
scrapy crawl ebay_sold_items -a search_query="size 9 nikes" -O output.json

# CSV format
scrapy crawl ebay_sold_items -a search_query="size 9 nikes" -O output.csv

# JSON format with max_items arg
scrapy crawl ebay_sold_items -a search_query="size 9 nikes" -a max_items=100 -O output.json

# CSV format with max_items arg
scrapy crawl ebay_sold_items -a search_query="size 9 nikes" -a max_items=100 -O output.csv
```

## Database

The scraper stores data in an SQLite database located at `database/ebay_sold_items.db`. The database schema includes:

- `item_id` (Primary Key)
- `item_url`
- `image_url`
- `title`
- `condition`
- `date_sold`
- `price`
- `shipping_cost`
- `shipping_location`
- `best_offer`
- `seller_name`
- `seller_feedback_score`
- `seller_feedback_percent`

## Error Handling

The scraper automatically captures screenshots when errors occur. Screenshots are saved in the `screenshots/` directory with timestamps and error types.
