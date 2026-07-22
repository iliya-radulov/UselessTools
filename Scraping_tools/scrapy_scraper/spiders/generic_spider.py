import scrapy
from datetime import datetime

class GenericSpider(scrapy.Spider):
    name = 'generic'
    results = []  # Class variable to store results across instances
    
    def __init__(self, url=None, selector=None, max_items=50, *args, **kwargs):
        super(GenericSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.selector = selector or ''
        self.max_items = max_items
        self.scrape_time = datetime.now().isoformat()
        
    def parse(self, response):
        self.logger.info(f'Parsing: {response.url}')
        
        # Extract title
        title = response.css('title::text').get()
        title = title.strip() if title else 'No title found'
        
        items = []
        
        if self.selector:
            # Use CSS selector
            elements = response.css(self.selector)
            count = 0
            
            for elem in elements:
                if count >= self.max_items:
                    break
                    
                text = elem.css('::text').get(default='').strip()
                html = elem.get()
                
                items.append({
                    'text': text,
                    'html': html[:500] + '...' if len(html) > 500 else html,
                    'position': count + 1,
                })
                count += 1
        else:
            # No selector - get all text
            all_text = response.css('body::text').getall()
            text = ' '.join([t.strip() for t in all_text if t.strip()])
            
            items.append({
                'text': text[:1000] + '...' if len(text) > 1000 else text,
                'html': response.text[:500] + '...' if len(response.text) > 500 else response.text,
                'position': 1,
            })
        
        # Create result
        result = {
            'url': response.url,
            'status': response.status,
            'title': title,
            'count': len(items),
            'data': items,
            'scrape_time': self.scrape_time
        }
        
        # Store in class variable
        GenericSpider.results.append(result)
        
        # Yield the result
        yield result
    
    def closed(self, reason):
        self.logger.info(f'Spider closed: {reason}')
        self.logger.info(f'Scraped {len(GenericSpider.results)} pages')
