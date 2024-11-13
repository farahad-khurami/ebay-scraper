import datetime
import os

import scrapy
from scrapy.http import TextResponse
from scrapy_playwright.page import PageMethod
from playwright._impl._errors import TimeoutError


class EbaySoldItemsSpider(scrapy.Spider):
    name = "ebay_sold_items"
    allowed_domains = ["www.ebay.co.uk"]
    start_urls = ["https://www.ebay.co.uk"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_scraped = 0
        self.total_results = None
        self.search_query = "nike airforce size 9"

    def start_requests(self):
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
        page = response.meta["playwright_page"]

        if self.total_results is None:
            self.total_results = self._extract_total_results(response)
            self.logger.info(
                f"Total results for search (Sold items): {self.total_results}"
            )

        while self.items_scraped < self.total_results:
            try:
                async for item in self._process_current_page(page):
                    yield item

                if not await self._go_to_next_page(page):
                    self.logger.info("No 'Next' button found, ending pagination.")
                    break
            except TimeoutError:
                await self._handle_timeout_error(page)
                return

        await page.close()

    def _get_initial_page_methods(self):
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
        total_results_text = response.css(
            "h1.srp-controls__count-heading span.BOLD::text"
        ).get()
        if total_results_text:
            return int(total_results_text.replace(",", ""))
        return 0

    async def _process_current_page(self, page):
        html_content = await page.content()
        response = TextResponse(url=page.url, body=html_content, encoding="utf-8")

        for item in response.css("li.s-item"):
            item_data = self._extract_item_data(item)
            if item_data:
                yield item_data
                self.items_scraped += 1

                if self.items_scraped >= self.total_results:
                    self.logger.info(
                        "Reached the total result count, stopping pagination."
                    )
                    await page.close()
                    return

    async def _go_to_next_page(self, page):
        next_button = await page.query_selector("a.pagination__next")
        if next_button:
            self.logger.info("Clicking 'Next' button to load more items")
            await next_button.click()
            await page.wait_for_selector(".srp-results")
            return True
        return False

    async def _handle_timeout_error(self, page):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/timeout_error_{timestamp}.png"
        os.makedirs("screenshots", exist_ok=True)
        await page.screenshot(path=screenshot_path)
        self.logger.error(
            f"Timeout error encountered. Screenshot saved as {screenshot_path}"
        )
        await page.close()

    def _extract_item_data(self, item):
        item_data = {
            "item_id": item.css("::attr(id)").get(),
            "item_url": item.css("div.s-item__image a::attr(href)").get(),
            "image_url": item.css("div.s-item__image img::attr(src)").get(),
            "title": item.css("div.s-item__title span::text").get(),
            "condition": item.css("span.SECONDARY_INFO::text").get(),
            "date_sold": item.css(
                "span.s-item__caption--signal.POSITIVE span::text"
            ).get(),
            "price": item.css("span.s-item__price span.POSITIVE::text").get(),
            "shipping_cost": item.css("span.s-item__shipping::text").get(),
            "best_offer": item.css(
                "span.s-item__dynamic.s-item__formatBestOfferEnabled::text"
            ).get(),
            "seller_info": item.css("span.s-item__seller-info-text::text").get(),
            "rating": item.css("div.x-star-rating .clipped::text").get(),
            "rating_count": item.css(
                "span.s-item__reviews-count span[aria-hidden='false']::text"
            ).get(),
        }

        if not item_data["item_id"] or item_data["title"] == "Shop on eBay":
            return None

        return item_data
