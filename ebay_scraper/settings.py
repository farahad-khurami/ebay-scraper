# Scrapy settings for ebay_scraper project

BOT_NAME = "ebay_scraper"

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(levelname)s: %(message)s"

SPIDER_MODULES = ["ebay_scraper.spiders"]
NEWSPIDER_MODULE = "ebay_scraper.spiders"

# Obey robots.txt rules - consider ethical scraping
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 2
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 8
CONCURRENT_REQUESTS_PER_IP = 8

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 2
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = True

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Rotating tor proxy and rotating middleware settings
DOWNLOADER_MIDDLEWARES = {
    "scrapy_user_agents.middlewares.RandomUserAgentMiddleware": 400,
    "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
    "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
}

ROTATING_PROXY_LIST_PATH = "tor_proxy/proxy_list.txt"
ROTATING_PROXY_PAGE_RETRY_TIMES = 5

# Enable cookies
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# Configure item pipelines
ITEM_PIPELINES = {
    "ebay_scraper.pipelines.EbaySoldItemsPipeline": 300,
}
