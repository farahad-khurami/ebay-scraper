from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_spiders():
    """
    Runs multiple instances of the eBay spider with different arguments.
    """
    process = CrawlerProcess(get_project_settings())

    instances = [
        {"search_query": "pokemon cards", "max_items": 100},
        {"search_query": "rolex", "max_items": 100},
        {"search_query": "lego minecraft", "max_items": 100},
        {"search_query": "nintendo switch", "max_items": 100},
    ]

    for instance in instances:
        process.crawl("ebay_sold_items", **instance)

    # Start the crawling process
    process.start()

if __name__ == "__main__":
    run_spiders()
