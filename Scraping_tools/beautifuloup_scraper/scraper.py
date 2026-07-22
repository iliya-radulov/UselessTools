import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional

class BeautifulSoupScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_website(self, url: str, selector: str = None, element_type: str = None) -> Dict:
        """
        Scrape a website using Beautiful Soup
        
        Args:
            url: The URL to scrape
            selector: CSS selector (optional)
            element_type: Specific element to extract (e.g., 'h1', 'p', 'a')
        
        Returns:
            Dict with scraped data and metadata
        """
        try:
            # Fetch the page
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse with Beautiful Soup
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract data based on parameters
            result = {
                'url': url,
                'status_code': response.status_code,
                'title': soup.title.string if soup.title else 'No title found',
                'data': [],
                'metadata': {
                    'timestamp': time.time(),
                    'content_length': len(response.content)
                }
            }
            
            # If selector is provided, use it
            if selector:
                elements = soup.select(selector)
                result['data'] = [elem.get_text(strip=True) for elem in elements[:50]]  # Limit to 50
                result['count'] = len(elements)
            
            # If element type is provided, use it
            elif element_type:
                elements = soup.find_all(element_type)
                result['data'] = [elem.get_text(strip=True) for elem in elements[:50]]
                result['count'] = len(elements)
            
            # If neither, get all text
            else:
                result['data'] = [soup.get_text(strip=True)[:1000]]  # First 1000 chars
                result['count'] = 1
            
            return result
            
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}', 'url': url}
        except Exception as e:
            return {'error': f'Scraping failed: {str(e)}', 'url': url}
    
    def scrape_advanced(self, url: str, options: Dict) -> Dict:
        """
        Advanced scraping with multiple options
        
        Options:
            - extract_links: bool
            - extract_images: bool
            - extract_metadata: bool
            - custom_css: str
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            
            result = {'url': url, 'data': {}}
            
            if options.get('extract_links', False):
                links = soup.find_all('a', href=True)
                result['data']['links'] = [link['href'] for link in links[:20]]
            
            if options.get('extract_images', False):
                images = soup.find_all('img', src=True)
                result['data']['images'] = [img['src'] for img in images[:20]]
            
            if options.get('extract_metadata', False):
                meta_tags = soup.find_all('meta')
                result['data']['metadata'] = {
                    meta.get('name', meta.get('property', 'unknown')): meta.get('content', '')
                    for meta in meta_tags[:10]
                }
            
            if options.get('custom_css'):
                elements = soup.select(options['custom_css'])
                result['data']['custom'] = [elem.get_text(strip=True) for elem in elements[:50]]
            
            return result
            
        except Exception as e:
            return {'error': str(e), 'url': url}