import datetime
import os

import scrapy
from scrapy.http import TextResponse
from scrapy_playwright.page import PageMethod
from playwright._impl._errors import TimeoutError

from .constants import PageSelectors


class EbaySoldItemsSpider(scrapy.Spider):
    """
    A Scrapy spider to scrape sold items data from eBay UK.

    This spider uses Playwright for content rendering and supports
    features such as pagination, error handling, and optional proxy rotation.

    Attributes:
        name (str): The name of the spider.
        start_urls (list): The initial URL(s) to start scraping.
        max_items (int, optional): The maximum number of items to scrape.
        search_query (str): The search query for eBay (required).
        items_scraped (int): Counter for the number of items scraped.
        total_results (int, optional): Total number of results for the query.
    """

    name = "ebay_sold_items"
    start_urls = ["https://www.ebay.co.uk"]

    def __init__(self, max_items=None, search_query=None, *args, **kwargs):
        """
        Initialises the spider with optional max_items and required search_query.

        Args:
            max_items (int, optional): The maximum number of items to scrape.
            search_query (str): The search query for eBay (required).

        Raises:
            ValueError: If the search_query argument is not provided.
        """
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

    def start_requests(self):
        """
        Generates the initial request to the start URL.

        Yields:
            scrapy.Request: A Scrapy request object with Playwright enabled.
        """
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": self._get_initial_page_methods(),
            },
            callback=self.parse,
        )

    async def parse(self, response):
        """
        Parses the response and handles pagination to scrape items.

        Args:
            response (scrapy.http.Response): The response object from the initial request.

        Yields:
            dict: A dictionary containing scraped item data.
        """
        page = response.meta["playwright_page"]

        if self.total_results is None:
            self.total_results = self._extract_total_results(response)
            self.logger.info(
                f"Total results for search (Sold items): {self.total_results}"
            )

        while self.items_scraped < self.total_results:
            if self.max_items and self.items_scraped >= self.max_items:
                self.logger.info("Reached max_items limit, stopping pagination.")
                break

            try:
                async for item in self._process_current_page(page):
                    yield item

                if not await self._go_to_next_page(page):
                    self.logger.info("No 'Next' button found, ending pagination.")
                    break
            except TimeoutError:
                await self._handle_timeout_error(page)
                break

        self.logger.info(
            f"Scraping session ended. Total items scraped: {self.items_scraped}"
        )
        await page.close()

    def _get_initial_page_methods(self):
        """
        Defines the sequence of actions to perform on the initial page.

        Returns:
            list: A list of Playwright PageMethod objects.
        """
        return [
            PageMethod("wait_for_selector", PageSelectors.GDPR_BANNER_ACCEPT),
            PageMethod("click", PageSelectors.GDPR_BANNER_ACCEPT),
            PageMethod("wait_for_load_state", "networkidle"),
            PageMethod("fill", PageSelectors.SEARCH_BAR, self.search_query),
            PageMethod("wait_for_timeout", 1000),
            PageMethod("press", PageSelectors.SEARCH_BAR, "Enter"),
            PageMethod("wait_for_selector", PageSelectors.SEARCH_RESULTS_CONTAINER),
            PageMethod("wait_for_selector", PageSelectors.SOLD_ITEMS_FILTER),
            PageMethod("click", PageSelectors.SOLD_ITEMS_FILTER),
            PageMethod("wait_for_selector", PageSelectors.RESULTS_COUNT_HEADING),
        ]

    def _extract_total_results(self, response):
        """
        Extracts the total number of results from the response.

        Args:
            response (scrapy.http.Response): The response object.

        Returns:
            int: The total number of results, or 0 if not found.
        """
        total_results_text = response.css(
            f"{PageSelectors.RESULTS_COUNT_HEADING} span.BOLD::text"
        ).get()
        if total_results_text:
            return int(total_results_text.replace(",", ""))
        return 0

    async def _process_current_page(self, page):
        """
        Processes the current page to extract item data.

        Args:
            page (playwright.async_api.Page): The Playwright page object.

        Yields:
            dict: A dictionary containing scraped item data.
        """
        html_content = await page.content()
        response = TextResponse(url=page.url, body=html_content, encoding="utf-8")

        for item in response.css(PageSelectors.ITEM_SELECTOR):
            item_data = self._extract_item_data(item)
            if item_data:
                yield item_data
                self.items_scraped += 1

                if self.max_items and self.items_scraped >= self.max_items:
                    self.logger.info(
                        "Reached the max_items limit, stopping pagination."
                    )
                    return

    async def _go_to_next_page(self, page):
        """
        Navigates to the next page if the 'Next' button is found.

        Args:
            page (playwright.async_api.Page): The Playwright page object.

        Returns:
            bool: True if navigation to the next page was successful, False otherwise.
        """
        next_button = await page.query_selector(PageSelectors.NEXT_BUTTON)
        if next_button:
            self.logger.info("Clicking 'Next' button to load more items")
            await page.wait_for_timeout(500)
            await next_button.click()
            await page.wait_for_selector(PageSelectors.SEARCH_RESULTS_CONTAINER)
            return True
        return False

    async def _handle_timeout_error(self, page):
        """
        Handles timeout errors by taking a screenshot and stopping the spider.

        Args:
            page (playwright.async_api.Page): The Playwright page object.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/timeout_error_{timestamp}.png"
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path=screenshot_path)
        self.logger.error(
            f"Timeout error encountered. Screenshot saved as {screenshot_path}"
        )
        await page.close()

    def _extract_item_data(self, item):
        """
        Extracts data for a single item from the response.

        Args:
            item (scrapy.selector.Selector): The selector for the item.

        Returns:
            dict: A dictionary containing item data, or None if invalid.
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
