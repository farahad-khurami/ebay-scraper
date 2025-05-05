# Seems to be a hardlimit of 200 pages that ebay will show you before it stops showing sold items
import random
import re
import urllib.parse

import scrapy
from scrapy.http import Request
from .constants import PageSelectors


class EbaySoldItemsSpider(scrapy.Spider):
    name = "ebay_sold_items"
    start_urls = ["https://www.ebay.co.uk"]
    
    def __init__(self, max_items=None, search_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not search_query:
            raise ValueError(
                "The 'search_query' argument is required. Please provide it using -a search_query=\"<value>\". "
                '\nExample: -a search_query="size 9 nikes"'
            )
        self.max_items = int(max_items) if max_items else None
        self.search_query = search_query
        self.items_scraped = 0
        self.total_results = None
        self.last_pause_checkpoint = 0

    def start_requests(self):
        yield Request(
            url=self.start_urls[0],
            callback=self.parse_homepage
        )
    
    def parse_homepage(self, response):
        self.logger.info("Successfully loaded homepage")
        
        search_url = f"https://www.ebay.co.uk/sch/i.html?_nkw={urllib.parse.quote_plus(self.search_query)}&_ipg=240"
        
        self.logger.info(f"Searching for: {self.search_query}")
        
        yield Request(
            url=search_url,
            callback=self.parse_search_results
        )
    
    def parse_search_results(self, response):
        self.logger.info("Processing search results page")

        sold_filter_url = None
        for link in response.css('a::attr(href)').getall():
            if 'LH_Sold=1' in link:
                sold_filter_url = response.urljoin(link)
                break
        
        if not sold_filter_url:
            current_url = response.url
            if '?' in current_url:
                sold_filter_url = f"{current_url}&LH_Sold=1"
            else:
                sold_filter_url = f"{current_url}?LH_Sold=1"
        
        self.logger.info(f"Applying sold items filter: {sold_filter_url}")
        
        yield Request(
            url=sold_filter_url,
            callback=self.parse_filtered_results
        )
    
    def parse_filtered_results(self, response):
        self.logger.info(f"Processing search results page: {response.url}")
        
        if self.total_results is None:
            self.total_results = self._extract_total_results(response)
            self.logger.info(f"Total results for search (Sold items): {self.total_results}")
        
        items_on_page = 0
        for item in response.css(PageSelectors.ITEM_SELECTOR):
            item_data = self._extract_item_data(item)
            if item_data:
                yield item_data
                self.items_scraped += 1
                items_on_page += 1
                
                if self.max_items and self.items_scraped >= self.max_items:
                    self.logger.info(f"Reached max_items limit ({self.max_items}), stopping pagination.")
                    self.logger.info(f"Total items scraped so far: {self.items_scraped}")
                    return
        
        self.logger.info(f"Items scraped on this page: {items_on_page}")
        self.logger.info(f"Total items scraped so far: {self.items_scraped}")
        self.logger.info(f"")
        
        self._check_for_pause()
        
        next_page_url = response.css(f"{PageSelectors.NEXT_BUTTON}::attr(href)").get()
        if next_page_url and (not self.max_items or self.items_scraped < self.max_items):
            next_page_url = response.urljoin(next_page_url)
            self.logger.info(f"Moving to next page: {next_page_url}")
            
            yield Request(
                url=next_page_url,
                callback=self.parse_filtered_results,
                dont_filter=True,
                # meta={"download_delay": random.uniform(2, 4)}  # Random delay between requests
            )
        else:
            self.logger.info("No more pages to scrape or reached item limit.")
    
    def _check_for_pause(self):
        """
        Checks if the scraper should pause based on the number of items scraped.
        Pauses for 5-10 seconds every 900-1000 items.
        """
        random_number = random.randint(700, 1000)
        current_checkpoint = self.items_scraped // random_number
        
        # If we've passed a new checkpoint and it's not the same as the last one
        if current_checkpoint > self.last_pause_checkpoint:
            # Update the checkpoint
            self.last_pause_checkpoint = current_checkpoint
            
            sleep_time = random.uniform(0, 1.5)
            self.logger.info(f"Taking a break after scraping {self.items_scraped} items.")
            self.logger.info(f"Pausing for {sleep_time:.2f} seconds...")
    
    def _extract_total_results(self, response):
        """
        Extracts the total number of results from the response.
        """
        total_results_text = response.css(
            f"{PageSelectors.RESULTS_COUNT_HEADING} span.BOLD::text"
        ).get()
        
        if total_results_text:
            return int(total_results_text.replace(",", ""))
        
        match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+results', response.text)
        if match:
            return int(match.group(1).replace(",", ""))
        
        return 0
    
    def _extract_item_data(self, item):
        """
        Extracts data for a single item from the response.
        """
        item_data = {
            "item_id": item.css(PageSelectors.ITEM_ID).get(),
            "item_url": item.css(PageSelectors.ITEM_URL).get(),
            "image_url": item.css(PageSelectors.IMAGE_URL).get(),
            "title": item.css(PageSelectors.TITLE).get(),
            "condition": item.css(PageSelectors.CONDITION).get(),
            "date_sold": item.css(PageSelectors.DATE_SOLD).get(),
            "price": item.css(PageSelectors.PRICE).get(),
            "shipping_cost": item.css(PageSelectors.SHIPPING_COST).get()
            or item.css(PageSelectors.SHIPPING_COST_ALT).get(),
            "shipping_location": item.css(PageSelectors.SHIPPING_LOCATION).get(),
            "best_offer": item.css(PageSelectors.BEST_OFFER).get(),
            "seller_info": item.css(PageSelectors.SELLER_INFO).get(),
        }
        
        if not item_data["item_id"] or item_data["title"] == "Shop on eBay":
            return None
        
        return item_data