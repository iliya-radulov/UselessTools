from flask import Flask, render_template, request, jsonify
from scraper import BeautifulSoupScraper
import json

app = Flask(__name__)
scraper = BeautifulSoupScraper()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle scraping requests"""
    try:
        data = request.get_json()
        url = data.get('url')
        method = data.get('method', 'basic')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Different scraping methods
        if method == 'basic':
            selector = data.get('selector')
            element_type = data.get('element_type')
            result = scraper.scrape_website(url, selector, element_type)
        
        elif method == 'advanced':
            options = data.get('options', {})
            result = scraper.scrape_advanced(url, options)
        
        else:
            return jsonify({'error': 'Invalid method'}), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
def preview():
    """Preview a website without full scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        # Just get the title and basic info
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.content, 'lxml')
        
        return jsonify({
            'title': soup.title.string if soup.title else 'No title',
            'status': response.status_code,
            'content_type': response.headers.get('content-type', 'unknown')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)