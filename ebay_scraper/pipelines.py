import os
import re
import sqlite3
from datetime import datetime


class EbaySoldItemsPipeline:
    def open_spider(self, spider):
        self._initialise_database()

    def close_spider(self, spider):
        self._close_database_connection()

    def process_item(self, item, spider):
        item["price"] = self._convert_price_to_float(item.get("price"))
        item["date_sold"] = self._standardise_date(item.get("date_sold"))

        self._insert_item_into_database(item)
        return item

    def _initialise_database(self):
        os.makedirs("database", exist_ok=True)

        self.connection = sqlite3.connect("database/ebay_sold_items.db")
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sold_items (
                item_id TEXT PRIMARY KEY,
                item_url TEXT,
                image_url TEXT,
                title TEXT,
                condition TEXT,
                date_sold TEXT,
                price REAL,
                shipping_cost TEXT,
                best_offer TEXT,
                seller_info TEXT,
                rating REAL,
                rating_count INTEGER
            )
            """
        )
        self.connection.commit()

    def _close_database_connection(self):
        self.connection.commit()
        self.connection.close()

    def _insert_item_into_database(self, item):
        self.cursor.execute(
            """
            INSERT OR IGNORE INTO sold_items (
                item_id, item_url, image_url, title, condition, date_sold, 
                price, shipping_cost, best_offer, seller_info, rating, rating_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("item_id"),
                item.get("item_url"),
                item.get("image_url"),
                item.get("title"),
                item.get("condition"),
                item.get("date_sold"),
                item.get("price"),
                item.get("shipping_cost"),
                item.get("best_offer"),
                item.get("seller_info"),
                item.get("rating"),
                item.get("rating_count"),
            ),
        )
        self.connection.commit()

    def _convert_price_to_float(self, price_str):
        if not price_str:
            return None
        cleaned_price = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(cleaned_price)
        except ValueError:
            return None

    def _standardise_date(self, date_str):
        if not date_str:
            return None
        # Convert date from format "Sold DD MMM YYYY" to "YYYY-MM-DD"
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
