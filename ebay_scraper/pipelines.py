import re
from datetime import datetime


class EbaySoldItemsPipeline:
    def process_item(self, item, spider):
        if item.get("price"):
            item["price"] = self._convert_price_to_float(item["price"])

        if item.get("date_sold"):
            item["date_sold"] = self._standardise_date(item["date_sold"])

        return item

    def _convert_price_to_float(self, price_str):
        cleaned_price = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(cleaned_price)
        except ValueError:
            return None

    def _standardise_date(self, date_str):
        # Original date format "Sold DD MMM YYYY", converting to "YYYY-MM-DD"
        match = re.search(r"Sold\s+(\d{1,2})\s+(\w+)\s+(\d{4})", date_str)
        if match:
            day, month_str, year = match.groups()
            try:
                month = datetime.strptime(month_str, "%b").month
                standardised_date = datetime(int(year), month, int(day))
                return standardised_date.strftime("%Y-%m-%d")
            except ValueError:
                return None
        return None
