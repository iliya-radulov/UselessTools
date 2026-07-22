import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
from scrapy_project.items import ScrapedPage, ScrapedItem
from datetime import datetime
import json
import re

class GenericSpider(scrapy.Spider):
    """
    Generic spider that can scrape any website with CSS selectors
    """
    name = 'generic'
    
    def __init__(self, url=None, selector=None, max_items=50, *args, **kwargs):
        super(GenericSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.selector = selector or ''
        self.max_items = max_items
        self.results = []
        self.scrape_time = datetime.now().isoformat()
        
    def parse(self, response):
        """Parse the response and extract data"""
        self.logger.info(f'Parsing: {response.url}')
        
        # Extract page-level data
        page_data = ScrapedPage()
        page_data['url'] = response.url
        page_data['status'] = response.status
        page_data['scrape_time'] = self.scrape_time
        
        # Extract title
        title = response.css('title::text').get()
        page_data['title'] = title.strip() if title else 'No title found'
        
        # Extract items based on selector
        items = []
        
        if self.selector:
            # Use CSS selector
            elements = response.css(self.selector)
            count = 0
            
            for elem in elements:
                if count >= self.max_items:
                    break
                    
                item = ScrapedItem()
                item['url'] = response.url
                item['title'] = page_data['title']
                item['selector_used'] = self.selector
                item['timestamp'] = datetime.now().isoformat()
                
                # Extract text
                text = elem.css('::text').get(default='').strip()
                item['text'] = text
                
                # Extract HTML
                html = elem.get()
                item['html'] = html if len(html) < 1000 else html[:1000] + '...'
                
                # Extract metadata
                item['metadata'] = {
                    'position': count + 1,
                    'tag': elem.root.tag if hasattr(elem.root, 'tag') else 'unknown',
                    'classes': elem.root.get('class', []) if hasattr(elem.root, 'get') else [],
                    'id': elem.root.get('id', '') if hasattr(elem.root, 'get') else '',
                }
                
                items.append(item)
                count += 1
                
        else:
            # No selector - get all text
            item = ScrapedItem()
            item['url'] = response.url
            item['title'] = page_data['title']
            item['selector_used'] = 'all_text'
            item['timestamp'] = datetime.now().isoformat()
            
            # Get all text
            all_text = response.css('body::text').getall()
            text = ' '.join([t.strip() for t in all_text if t.strip()])
            item['text'] = text[:1000] + '...' if len(text) > 1000 else text
            
            # Get HTML preview
            html = response.text
            item['html'] = html[:1000] + '...' if len(html) > 1000 else html
            
            item['metadata'] = {
                'position': 1,
                'tag': 'body',
                'classes': [],
                'id': '',
            }
            
            items.append(item)
        
        page_data['items'] = items
        page_data['total_items'] = len(items)
        
        # Store result
        self.results.append({
            'url': response.url,
            'status': response.status,
            'title': page_data['title'],
            'count': len(items),
            'data': [item.asdict() if hasattr(item, 'asdict') else item for item in items],
            'scrape_time': self.scrape_time
        })
        
        yield page_data
        
        # Yield each item individually for pipelines
        for item in items:
            yield item
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f'Spider closed: {reason}')
        self.logger.info(f'Scraped {len(self.results)} pages')
        
        # Log summary
        for result in self.results:
            self.logger.info(f'  - {result["url"]}: {result["count"]} items')