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
        {"search_query": "lego" },
        {"search_query": "nintendo switch"},
        {"search_query": "RTX 4090 graphics card"},
        {"search_query": "iPhone 15"},
        {"search_query": "MacBook Pro"},
        {"search_query": "gaming PC"},
        {"search_query": "Labubu plush"},
        {"search_query": "Jellycat plush"},
        {"search_query": "Air Jordan sneakers"},
        {"search_query": "Funko Pop"},
        {"search_query": "GoPro Hero"},
        {"search_query": "Apple Watch"},
        {"search_query": "Samsung Galaxy S23"},
        {"search_query": "vintage vinyl records"},
        {"search_query": "wireless earbuds"},
        {"search_query": "Bose headphones"},
        {"search_query": "gaming keyboard"},
        {"search_query": "LED strip lights"},
    ]

    for instance in instances:
        process.crawl("ebay_sold_items", **instance)

    # Start the crawling process
    process.start()

if __name__ == "__main__":
    run_spiders()
