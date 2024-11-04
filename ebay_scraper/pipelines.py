# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import re
from datetime import datetime

class EbaySoldItemsPipeline:
    def process_item(self, item, spider):
        # Convert price to float
        if item.get("price"):
            item["price"] = self.convert_price_to_float(item["price"])

        # Standardize date_sold
        if item.get("date_sold"):
            item["date_sold"] = self.standardize_date(item["date_sold"])

        return item

    def convert_price_to_float(self, price_str):
        # Remove currency symbols and commas, then convert to float
        cleaned_price = re.sub(r"[^\d.]", "", price_str)  # Remove everything except numbers and decimal point
        try:
            return float(cleaned_price)
        except ValueError:
            return None  # Return None if conversion fails

    def standardize_date(self, date_str):
        # Assuming the format "Sold DD MMM YYYY" and converting to "YYYY-MM-DD"
        match = re.search(r"Sold\s+(\d{1,2})\s+(\w+)\s+(\d{4})", date_str)
        if match:
            day, month_str, year = match.groups()
            try:
                # Convert the extracted date to "YYYY-MM-DD"
                month = datetime.strptime(month_str, "%b").month  # Convert month name to month number
                standardized_date = datetime(int(year), month, int(day))
                return standardized_date.strftime("%Y-%m-%d")
            except ValueError:
                return None  # Return None if date conversion fails
        return None