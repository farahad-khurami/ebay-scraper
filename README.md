# eBay Sold Items Scraper

A web scraper built with Scrapy and Playwright to extract sold items data from eBay UK. Features rotating Tor proxies, anti-bot measures, and SQLite storage.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ebay-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Set up Tor proxies:
```bash
cd tor_proxy
python tor_proxy_setup.py
docker compose up -d
```

## Configuration

### Spider Settings
The main settings can be found in `ebay_scraper/settings.py`:

- `CONCURRENT_REQUESTS`: Maximum concurrent requests (default: 16)
- `AUTOTHROTTLE_ENABLED`: Enable/disable automatic throttling
- `AUTOTHROTTLE_START_DELAY`: Initial download delay
- `AUTOTHROTTLE_MAX_DELAY`: Maximum download delay
- `PLAYWRIGHT_LAUNCH_OPTIONS`: Playwright browser options
- `ROTATING_PROXY_LIST_PATH`: Path to proxy list
- `ROTATING_PROXY_PAGE_RETRY_TIMES`: Number of retries per proxy

### Search Query
To modify the search query, edit the `search_query` variable in `ebay_scraper/spiders/ebay_sold_items.py`:

```python
def __init__(self, max_items=None, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.search_query = "ps5"  # Change this to your desired search term
```

## Usage

### Basic Usage
Run the spider from the root of the repo:
```bash
scrapy crawl ebay_sold_items
```

### Limit Number of Items
Specify maximum number of items to scrape (optional):
```bash
scrapy crawl ebay_sold_items -a max_items=100
```

### Output Formats
Save results to CSV or Json. Recommend you use this with `max_items` arg:
```bash
# JSON format
scrapy crawl ebay_sold_items -O output.json

# CSV format
scrapy crawl ebay_sold_items -O output.csv

# JSON format with max_items arg
scrapy crawl ebay_sold_items -a max_items=100 -O output.json

# CSV format with max_items arg
scrapy crawl ebay_sold_items -a max_items=100 -O output.csv
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


## Troubleshooting

### Common Issues

1. **Proxy Connection Errors**
   - Ensure Docker containers are running
   - Check proxy list file exists
   - Verify Docker network connectivity

2. **Browser Launch Failures**
   - Ensure Playwright browsers are installed
   - Check system resources
   - Verify Python environment

3. **Rate Limiting**
   - Increase `AUTOTHROTTLE_START_DELAY`
   - Reduce `CONCURRENT_REQUESTS`
   - Check proxy rotation



