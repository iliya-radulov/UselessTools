import scrapy

class ScrapedItem(scrapy.Item):
    """Define the data structure for scraped items"""
    url = scrapy.Field()
    title = scrapy.Field()
    text = scrapy.Field()
    html = scrapy.Field()
    selector_used = scrapy.Field()
    timestamp = scrapy.Field()
    metadata = scrapy.Field()
    
class ScrapedPage(scrapy.Item):
    """Page-level data"""
    url = scrapy.Field()
    status = scrapy.Field()
    title = scrapy.Field()
    items = scrapy.Field()  # List of ScrapedItem
    total_items = scrapy.Field()
    scrape_time = scrapy.Field()