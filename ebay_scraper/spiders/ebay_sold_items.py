import datetime
import os

import scrapy
from scrapy.http import TextResponse
from scrapy_playwright.page import PageMethod
from playwright._impl._errors import TimeoutError


class EbaySoldItemsSpider(scrapy.Spider):
    name = "ebay_sold_items"  # Name of the spider
    allowed_domains = ["www.ebay.co.uk"]  # Restrict scraping to these domains
    start_urls = ["https://www.ebay.co.uk"]  # Initial URL to start scraping

    def __init__(self, max_items=None, search_query=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not search_query:
            raise ValueError(
                "The 'search_query' argument is required. Please provide it using -a search_query=\"<value>\". "
                "\nExample: -a search_query=\"size 9 nikes\""
            )
        self.max_items = int(max_items) if max_items else None
        self.search_query = search_query
        self.items_scraped = 0 
        self.total_results = None

    def start_requests(self):
        # Initial request with Playwright enabled to handle dynamic content
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,  # Enable Playwright for this request
                "playwright_include_page": True,  # Include the Playwright page object
                "playwright_page_methods": self._get_initial_page_methods(),  # Methods to execute on the page
            },
            callback=self.parse,  # Callback to handle the response
        )

    async def parse(self, response):
        # Main parsing logic to handle results and pagination
        page = response.meta["playwright_page"]

        if self.total_results is None:
            # Extract total results if not already extracted
            self.total_results = self._extract_total_results(response)
            self.logger.info(
                f"Total results for search (Sold items): {self.total_results}"
            )

        # Loop until all items are scraped, max_items is reached, or pagination ends
        while self.items_scraped < self.total_results:
            if self.max_items and self.items_scraped >= self.max_items:
                self.logger.info("Reached max_items limit, stopping pagination.")
                break

            try:
                # Process current page and yield scraped items
                async for item in self._process_current_page(page):
                    yield item

                # Navigate to the next page if possible
                if not await self._go_to_next_page(page):
                    self.logger.info("No 'Next' button found, ending pagination.")
                    break
            except TimeoutError:
                # Handle timeout errors by taking a screenshot and stopping
                await self._handle_timeout_error(page)
                break

        # Log the total number of items scraped
        self.logger.info(
            f"Scraping session ended. Total items scraped: {self.items_scraped}"
        )

        # Close the Playwright page after scraping is complete
        await page.close()

    def _get_initial_page_methods(self):
        # Define the sequence of actions to perform on the initial page
        return [
            PageMethod("wait_for_selector", "#gdpr-banner-accept"),
            PageMethod("click", "#gdpr-banner-accept"),
            PageMethod("wait_for_load_state", "networkidle"),
            PageMethod("fill", "#gh-ac", self.search_query),
            PageMethod("wait_for_timeout", 300),
            PageMethod("press", "#gh-ac", "Enter"),
            PageMethod("wait_for_selector", ".srp-results"),
            PageMethod(
                "wait_for_selector",
                "span.cbx.x-refine__multi-select-cbx:has-text('Sold items')",
            ),
            PageMethod(
                "click",
                "span.cbx.x-refine__multi-select-cbx:has-text('Sold items')",
            ),
            PageMethod("wait_for_selector", "h1.srp-controls__count-heading"),
        ]

    def _extract_total_results(self, response):
        # Extract the total number of results from the response
        total_results_text = response.css(
            "h1.srp-controls__count-heading span.BOLD::text"
        ).get()
        if total_results_text:
            return int(total_results_text.replace(",", ""))  # Convert to integer
        return 0  # Default to 0 if extraction fails

    async def _process_current_page(self, page):
        # Process the current page and yield items
        html_content = await page.content()  # Get the page's HTML content
        response = TextResponse(
            url=page.url, body=html_content, encoding="utf-8"
        )  # Create a TextResponse object

        # Extract items from the current page
        for item in response.css("li.s-item"):
            item_data = self._extract_item_data(item)  # Extract item data
            if item_data:
                yield item_data  # Yield the item data
                self.items_scraped += 1  # Increment the scraped items counter

                # Stop if the maximum number of items has been reached
                if self.max_items and self.items_scraped >= self.max_items:
                    self.logger.info(
                        "Reached the max_items limit, stopping pagination."
                    )
                    return

    async def _go_to_next_page(self, page):
        # Navigate to the next page if the 'Next' button is found
        next_button = await page.query_selector("a.pagination__next")
        if next_button:
            self.logger.info("Clicking 'Next' button to load more items")
            await next_button.click()  # Click the 'Next' button
            await page.wait_for_selector(".srp-results")  # Wait for the results to load
            return True
        return False

    async def _handle_timeout_error(self, page):
        # Handle timeout errors by taking a screenshot and logging the error
        timestamp = datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )  # Generate a timestamp
        screenshot_path = (
            f"screenshots/timeout_error_{timestamp}.png"  # Define screenshot path
        )
        os.makedirs(
            "screenshots", exist_ok=True
        )  # Create the screenshots directory if it doesn't exist
        await page.screenshot(path=screenshot_path)  # Take a screenshot
        self.logger.error(
            f"Timeout error encountered. Screenshot saved as {screenshot_path}"
        )
        await page.close()  # Close the Playwright page

    def _extract_item_data(self, item):
        # Extract data for a single item
        item_data = {
            "item_id": item.css("::attr(id)").get(),  # Extract the item ID
            "item_url": item.css("div.s-item__image a::attr(href)").get(),
            "image_url": item.css("div.s-item__image img::attr(src)").get(),
            "title": item.css("div.s-item__title span::text").get(),
            "condition": item.css("span.SECONDARY_INFO::text").get(),
            "date_sold": item.css(
                "span.s-item__caption--signal.POSITIVE span::text"
            ).get(),
            "price": item.css("span.s-item__price span.POSITIVE::text").get(),
            "shipping_cost": item.css(
                ".s-item__shipping.s-item__logisticsCost span::text"
            ).get()
            or item.css("span.s-item__shipping::text").get(),
            "shipping_location": item.css(
                ".s-item__location.s-item__itemLocation span::text"
            ).get(),
            "best_offer": item.css(
                "span.s-item__dynamic.s-item__formatBestOfferEnabled::text"
            ).get(),
            "seller_info": item.css("span.s-item__seller-info-text::text").get(),
        }

        if not item_data["item_id"] or item_data["title"] == "Shop on eBay":
            return None

        return item_data
