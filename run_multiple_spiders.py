from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def run_spiders():
    """
    Runs multiple instances of the eBay spider with different arguments.
    """
    process = CrawlerProcess(get_project_settings())

    instances = [
        {"search_query": "pokemon cards"},
        {"search_query": "rolex"},
        {"search_query": "lego minecraft"},
        {"search_query": "nintendo switch"},
    ]

    for instance in instances:
        process.crawl("ebay_sold_items", **instance)

    # Start the crawling process
    process.start()

if __name__ == "__main__":
    run_spiders()
