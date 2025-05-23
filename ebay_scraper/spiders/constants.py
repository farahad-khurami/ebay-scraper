class PageSelectors:
    # Main page selectors
    SEARCH_RESULTS_CONTAINER = ".srp-results"
    SOLD_ITEMS_FILTER = "span.cbx.x-refine__multi-select-cbx:has-text('Sold items')"
    RESULTS_COUNT_HEADING = "h1.srp-controls__count-heading"
    NEXT_BUTTON = "a.pagination__next"

    # Item selectors
    ITEM_SELECTOR = "li.s-item"
    ITEM_ID = "::attr(id)"
    ITEM_URL = "div.s-item__image a::attr(href)"
    IMAGE_URL = "div.s-item__image img::attr(src)"
    TITLE = "div.s-item__title span::text"
    CONDITION = "span.SECONDARY_INFO::text"
    DATE_SOLD = "span.s-item__caption--signal.POSITIVE span::text"
    PRICE = "span.s-item__price span.POSITIVE::text"
    SHIPPING_COST = ".s-item__shipping.s-item__logisticsCost span::text"
    SHIPPING_COST_ALT = "span.s-item__shipping::text"
    SHIPPING_LOCATION = ".s-item__location.s-item__itemLocation span::text"
    BEST_OFFER = "span.s-item__dynamic.s-item__formatBestOfferEnabled::text"
    SELLER_INFO = "span.s-item__seller-info-text::text"

    # Filters and URL parameters
    SOLD_ITEMS_PARAM = "LH_Sold=1"
    COMPLETED_ITEMS_PARAM = "LH_Complete=1"
