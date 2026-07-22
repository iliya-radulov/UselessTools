from itemadapter import ItemAdapter
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ScrapyProjectPipeline:
    """Process scraped items"""
    
    def open_spider(self, spider):
        self.items = []
        self.file = None
        
    def close_spider(self, spider):
        # Save all items to a JSON file
        if self.items:
            filename = f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w') as f:
                json.dump(self.items, f, indent=2, default=str)
            spider.logger.info(f'Saved {len(self.items)} items to {filename}')
    
    def process_item(self, item, spider):
        """Process each scraped item"""
        adapter = ItemAdapter(item)
        
        # Add timestamp if not present
        if 'timestamp' not in adapter:
            adapter['timestamp'] = datetime.now().isoformat()
        
        self.items.append(adapter.asdict())
        return item

class DuplicatesPipeline:
    """Remove duplicate items"""
    
    def __init__(self):
        self.ids_seen = set()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Create unique key
        key = f"{adapter.get('url')}_{adapter.get('text')}"
        
        if key in self.ids_seen:
            spider.logger.info(f'Duplicate item found: {key}')
            raise DropItem(f"Duplicate item found: {key}")
        else:
            self.ids_seen.add(key)
            return item