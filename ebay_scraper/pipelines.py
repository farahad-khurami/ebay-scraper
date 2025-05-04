import os
import re
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Integer,
    ForeignKey,
    DateTime,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import exists

Base = declarative_base()


class Search(Base):
    __tablename__ = "searches"

    search_id = Column(Integer, primary_key=True, autoincrement=True)
    search_term = Column(String, nullable=False)
    search_date = Column(DateTime, default=datetime.utcnow)

    # Relationship
    items = relationship("Item", back_populates="search")


class Seller(Base):
    __tablename__ = "sellers"

    seller_id = Column(Integer, primary_key=True, autoincrement=True)
    seller_username = Column(String, nullable=False, unique=True)
    feedback_score = Column(Integer)
    feedback_percent = Column(Float)

    # Relationship
    items = relationship("Item", back_populates="seller")


class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    ebay_item_id = Column(String, nullable=False, unique=True)
    search_id = Column(Integer, ForeignKey("searches.search_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("sellers.seller_id"), nullable=False)

    title = Column(String)
    item_url = Column(String)
    image_url = Column(String)
    condition = Column(String)
    sold_date = Column(DateTime)
    price = Column(Float)
    shipping_price = Column(Float)
    shipping_location = Column(String)
    best_offer = Column(String)

    # Relationships
    search = relationship("Search", back_populates="items")
    seller = relationship("Seller", back_populates="items")


class EbaySoldItemsPipeline:
    def open_spider(self, spider):
        self._initialise_database()
        self._get_or_create_search(spider.search_query)

    def close_spider(self, spider):
        self.session.close()
        self.engine.dispose()

    def process_item(self, item, spider):
        item["price"] = self._convert_price_to_float(item.get("price"))
        item["date_sold"] = self._standardise_date(item.get("date_sold"))
        item["shipping_cost"] = self._parse_shipping_cost(item.get("shipping_cost"))
        item["shipping_location"] = self._parse_shipping_location(
            item.get("shipping_location")
        )

        # Parse seller_info into separate fields
        seller_name, seller_feedback_score, seller_feedback_percent = (
            self._parse_seller_info(item.get("seller_info"))
        )
        item["seller_name"] = seller_name
        item["seller_feedback_score"] = seller_feedback_score
        item["seller_feedback_percent"] = seller_feedback_percent

        self._insert_item(item, spider.search_query)

        return item

    def _initialise_database(self):
        os.makedirs("database", exist_ok=True)
        self.engine = create_engine("sqlite:///database/ebay_sold_items.db")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def _get_or_create_search(self, search_term):
        # Find or create a search record for this crawl
        search = (
            self.session.query(Search)
            .filter_by(search_term=search_term)
            .order_by(Search.search_date.desc())
            .first()
        )

        if not search:
            search = Search(search_term=search_term)
            self.session.add(search)
            self.session.commit()

        self.current_search_id = search.search_id
        return search

    def _get_or_create_seller(self, seller_name, feedback_score, feedback_percent):
        # Find or create a seller record
        if not seller_name:
            seller_name = "Unknown Seller"

        seller = (
            self.session.query(Seller).filter_by(seller_username=seller_name).first()
        )

        if not seller:
            seller = Seller(
                seller_username=seller_name,
                feedback_score=feedback_score,
                feedback_percent=feedback_percent,
            )
            self.session.add(seller)
            self.session.commit()
        elif feedback_score is not None and feedback_percent is not None:
            seller.feedback_score = feedback_score
            seller.feedback_percent = feedback_percent
            self.session.commit()

        return seller

    def _insert_item(self, item, search_term):
        ebay_item_id = item.get("item_id")

        if self.session.query(
            exists().where(Item.ebay_item_id == ebay_item_id)
        ).scalar():
            return

        seller = self._get_or_create_seller(
            item.get("seller_name"),
            item.get("seller_feedback_score"),
            item.get("seller_feedback_percent"),
        )

        sold_date = None
        if item.get("date_sold"):
            try:
                sold_date = datetime.strptime(item.get("date_sold"), "%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        shipping_price = None
        if item.get("shipping_cost"):
            if item.get("shipping_cost") == "Free postage":
                shipping_price = 0.0
            else:
                try:
                    shipping_price = float(
                        re.sub(r"[^\d.]", "", item.get("shipping_cost"))
                    )
                except (ValueError, TypeError):
                    shipping_price = None

        new_item = Item(
            ebay_item_id=ebay_item_id,
            search_id=self.current_search_id,
            seller_id=seller.seller_id,
            title=item.get("title"),
            item_url=item.get("item_url"),
            image_url=item.get("image_url"),
            condition=item.get("condition"),
            sold_date=sold_date,
            price=item.get("price"),
            shipping_price=shipping_price,
            shipping_location=item.get("shipping_location"),
            best_offer=item.get("best_offer"),
        )

        self.session.add(new_item)
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

    def _parse_seller_info(self, seller_info):
        if not seller_info:
            return None, None, None

        match = re.match(r"([^()]+)\s+\(([\d,]+)\)\s+(\d+(\.\d+)?%)", seller_info)
        if match:
            seller_name = match.group(1).strip()
            seller_feedback_score = int(match.group(2).replace(",", ""))
            seller_feedback_percent = match.group(3).replace("%", "").strip()
            return seller_name, seller_feedback_score, float(seller_feedback_percent)

        return None, None, None

    def _parse_shipping_cost(self, shipping_cost):
        if not shipping_cost:
            return None
        translation_table = str.maketrans({"£": "", "+": ""})
        parsed_shipping_cost = (
            shipping_cost.translate(translation_table).replace("postage", "").strip()
        )
        return parsed_shipping_cost

    def _parse_shipping_location(self, shipping_location):
        if not shipping_location:
            return None
        parsed_shipping_location = shipping_location.replace("from", "").strip()
        return parsed_shipping_location
