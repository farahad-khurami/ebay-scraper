import os
import re
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class SoldItem(Base):
    __tablename__ = 'sold_items'

    item_id = Column(String, primary_key=True)
    item_url = Column(String)
    image_url = Column(String)
    title = Column(String)
    condition = Column(String)
    date_sold = Column(String)
    price = Column(Float)
    shipping_cost = Column(String)
    best_offer = Column(String)
    seller_info = Column(String)  # Raw seller info for reference
    seller_name = Column(String)
    seller_feedback_score = Column(Integer)
    seller_feedback_percent = Column(Float)
    rating = Column(Float)
    rating_count = Column(Integer)


class EbaySoldItemsPipeline:
    def open_spider(self, spider):
        self._initialise_database()

    def close_spider(self, spider):
        self.session.close()
        self.engine.dispose()

    def process_item(self, item, spider):
        item["price"] = self._convert_price_to_float(item.get("price"))
        item["date_sold"] = self._standardise_date(item.get("date_sold"))
        item["rating"] = self._extract_rating(item.get("rating"))

        # Parse seller_info into separate fields
        seller_name, seller_feedback_score, seller_feedback_percent = self._parse_seller_info(item.get("seller_info"))
        item["seller_name"] = seller_name
        item["seller_feedback_score"] = seller_feedback_score
        item["seller_feedback_percent"] = seller_feedback_percent

        self._insert_item_into_database(item)
        return item

    def _initialise_database(self):
        os.makedirs("database", exist_ok=True)
        self.engine = create_engine("sqlite:///database/ebay_sold_items.db")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _insert_item_into_database(self, item):
        sold_item = SoldItem(
            item_id=item.get("item_id"),
            item_url=item.get("item_url"),
            image_url=item.get("image_url"),
            title=item.get("title"),
            condition=item.get("condition"),
            date_sold=item.get("date_sold"),
            price=item.get("price"),
            shipping_cost=item.get("shipping_cost"),
            best_offer=item.get("best_offer"),
            seller_name=item.get("seller_name"),
            seller_feedback_score=item.get("seller_feedback_score"),
            seller_feedback_percent=item.get("seller_feedback_percent"),
            rating=item.get("rating"),
            rating_count=item.get("rating_count"),
        )

        if not self.session.query(SoldItem).filter_by(item_id=sold_item.item_id).first():
            self.session.add(sold_item)
            self.session.commit()

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

    def _extract_rating(self, rating_str):
        if not rating_str:
            return None
        match = re.search(r"(\d+(\.\d+)?)", rating_str)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _parse_seller_info(self, seller_info):
        match = re.match(r"([^()]+)\s+\(([\d,]+)\)\s+(\d+(\.\d+)?%)", seller_info)
        if match:
            seller_name = match.group(1).strip()
            seller_feedback_score = int(match.group(2).replace(",", ""))
            seller_feedback_percent = match.group(3).replace("%", "").strip()
            return seller_name, seller_feedback_score, float(seller_feedback_percent)
        return None, None, None