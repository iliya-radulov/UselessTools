# 🚀 Project 1: Beautiful Soup Web Scraper

```text
Tech Stack

    Backend: Flask (lightweight web framework)

    Scraping: requests + beautifulsoup4

    Frontend: Simple HTML/CSS with Bootstrap for styling

```

```text
📁 Project Structure
beautifulsoup-scraper/
├── app.py                 # Main Flask application
├── scraper.py             # Beautiful Soup scraping logic
├── templates/
│   └── index.html         # Frontend UI
├── static/
│   └── style.css          # Custom styles
├── requirements.txt       # Dependencies
└── .env                   # Environment variables (optional)
```


# 📦 Step 1: Install Dependencies

```text
Create requirements.txt:
txt

Flask==2.3.2
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
python-dotenv==1.0.0

Install them:
```

```bash
pip install -r requirements.txt
```

# 🧠 Step 2: The Scraper Logic

Create scraper.py:

```python

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
```

# 🌐 Step 3: The Flask App

Create app.py:

```python

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
```

# 🎨 Step 4: The Frontend

Create templates/index.html:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beautiful Soup Scraper</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        .scraped-data {
            max-height: 500px;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
        }
        .json-pretty {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .loading {
            display: none;
        }
        .progress-bar-striped {
            background-size: 1rem 1rem;
        }
    </style>
</head>
<body>
    <div class="container mt-5">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <h3 class="mb-0">
                            <i class="bi bi-file-code"></i> 
                            Beautiful Soup Scraper
                        </h3>
                        <small class="text-light">Simple HTML/XML parsing</small>
                    </div>
                    <div class="card-body">
                        <!-- URL Input -->
                        <div class="mb-3">
                            <label for="url" class="form-label">Website URL</label>
                            <div class="input-group">
                                <input type="url" class="form-control" id="url" 
                                       placeholder="https://example.com" 
                                       value="https://example.com">
                                <button class="btn btn-outline-secondary" type="button" id="previewBtn">
                                    <i class="bi bi-eye"></i> Preview
                                </button>
                            </div>
                            <div id="previewResult" class="mt-2 small text-muted"></div>
                        </div>

                        <!-- Scraping Options -->
                        <div class="mb-3">
                            <label class="form-label">Scraping Method</label>
                            <div class="btn-group w-100" role="group">
                                <input type="radio" class="btn-check" name="method" id="basicMethod" 
                                       value="basic" checked>
                                <label class="btn btn-outline-primary" for="basicMethod">
                                    <i class="bi bi-cpu"></i> Basic
                                </label>
                                <input type="radio" class="btn-check" name="method" id="advancedMethod" 
                                       value="advanced">
                                <label class="btn btn-outline-primary" for="advancedMethod">
                                    <i class="bi bi-gear"></i> Advanced
                                </label>
                            </div>
                        </div>

                        <!-- Basic Options -->
                        <div id="basicOptions" class="mb-3">
                            <div class="row">
                                <div class="col-md-6">
                                    <label for="selector" class="form-label">CSS Selector</label>
                                    <input type="text" class="form-control" id="selector" 
                                           placeholder=".main-content, #title, h1">
                                </div>
                                <div class="col-md-6">
                                    <label for="elementType" class="form-label">Element Type</label>
                                    <select class="form-select" id="elementType">
                                        <option value="">None</option>
                                        <option value="h1">H1</option>
                                        <option value="h2">H2</option>
                                        <option value="p">P</option>
                                        <option value="a">Links (A)</option>
                                        <option value="div">Div</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                        <!-- Advanced Options -->
                        <div id="advancedOptions" class="mb-3" style="display: none;">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="extractLinks">
                                        <label class="form-check-label" for="extractLinks">
                                            Extract Links
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="extractImages">
                                        <label class="form-check-label" for="extractImages">
                                            Extract Images
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="extractMetadata">
                                        <label class="form-check-label" for="extractMetadata">
                                            Extract Metadata
                                        </label>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <label for="customCss" class="form-label">Custom CSS</label>
                                    <input type="text" class="form-control" id="customCss" 
                                           placeholder=".custom-class #specific-id">
                                </div>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="d-grid gap-2">
                            <button class="btn btn-success btn-lg" id="scrapeBtn">
                                <i class="bi bi-play-circle"></i> Scrape Now
                            </button>
                            <button class="btn btn-secondary" id="clearBtn">
                                <i class="bi bi-eraser"></i> Clear Results
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Results Section -->
                <div class="card mt-4 shadow" id="resultCard" style="display: none;">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="bi bi-file-text"></i> Scraped Data</h5>
                    </div>
                    <div class="card-body">
                        <div id="loadingIndicator" class="text-center py-4" style="display: none;">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p class="mt-2">Scraping in progress...</p>
                        </div>
                        <div id="resultContent" class="scraped-data"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Toggle between basic and advanced options
        document.querySelectorAll('input[name="method"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'basic') {
                    document.getElementById('basicOptions').style.display = 'block';
                    document.getElementById('advancedOptions').style.display = 'none';
                } else {
                    document.getElementById('basicOptions').style.display = 'none';
                    document.getElementById('advancedOptions').style.display = 'block';
                }
            });
        });

        // Preview functionality
        document.getElementById('previewBtn').addEventListener('click', async function() {
            const url = document.getElementById('url').value;
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            const previewDiv = document.getElementById('previewResult');
            previewDiv.innerHTML = '<span class="text-info">Checking...</span>';

            try {
                const response = await fetch('/preview', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                const data = await response.json();
                
                if (data.error) {
                    previewDiv.innerHTML = `<span class="text-danger">⚠️ ${data.error}</span>`;
                } else {
                    previewDiv.innerHTML = `
                        <span class="text-success">✅ ${data.title}</span>
                        <span class="badge bg-info ms-2">Status: ${data.status}</span>
                        <span class="badge bg-secondary ms-2">${data.content_type}</span>
                    `;
                }
            } catch (error) {
                previewDiv.innerHTML = `<span class="text-danger">⚠️ ${error.message}</span>`;
            }
        });

        // Scrape functionality
        document.getElementById('scrapeBtn').addEventListener('click', async function() {
            const url = document.getElementById('url').value;
            const method = document.querySelector('input[name="method"]:checked').value;
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            // Show loading
            document.getElementById('resultCard').style.display = 'block';
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('resultContent').innerHTML = '';
            document.getElementById('scrapeBtn').disabled = true;

            try {
                let requestData = {url, method};
                
                if (method === 'basic') {
                    requestData.selector = document.getElementById('selector').value;
                    requestData.element_type = document.getElementById('elementType').value;
                } else {
                    requestData.options = {
                        extract_links: document.getElementById('extractLinks').checked,
                        extract_images: document.getElementById('extractImages').checked,
                        extract_metadata: document.getElementById('extractMetadata').checked,
                        custom_css: document.getElementById('customCss').value
                    };
                }

                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(requestData)
                });
                
                const data = await response.json();
                
                // Hide loading
                document.getElementById('loadingIndicator').style.display = 'none';
                
                // Display results
                const resultDiv = document.getElementById('resultContent');
                if (data.error) {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle"></i> ${data.error}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="mb-3">
                            <span class="badge bg-success">Status: ${data.status_code || 'N/A'}</span>
                            <span class="badge bg-info">${data.count || 0} items found</span>
                            <span class="badge bg-secondary">${data.title || 'No title'}</span>
                        </div>
                        <div class="json-pretty">
                            <strong>Data:</strong>
                            <pre>${JSON.stringify(data.data, null, 2)}</pre>
                        </div>
                        <div class="mt-3">
                            <strong>Metadata:</strong>
                            <pre>${JSON.stringify(data.metadata, null, 2)}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('loadingIndicator').style.display = 'none';
                document.getElementById('resultContent').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-x-circle"></i> ${error.message}
                    </div>
                `;
            } finally {
                document.getElementById('scrapeBtn').disabled = false;
            }
        });

        // Clear results
        document.getElementById('clearBtn').addEventListener('click', function() {
            document.getElementById('resultCard').style.display = 'none';
            document.getElementById('resultContent').innerHTML = '';
            document.getElementById('previewResult').innerHTML = '';
        });
    </script>
</body>
</html>
```

# 🚀 Step 5: Run It

```bash
python app.py
```
```text
Visit http://localhost:5000 in your browser.
🧪 Test It Out

Try these test URLs:

    Static site: https://example.com

    News site: https://news.ycombinator.com

    Simple Wikipedia: https://en.wikipedia.org/wiki/Web_scraping
```

```text
💡 Next Steps

Once this works, you can extend it by:

    Adding download functionality (CSV/JSON export)

    Adding scheduling capabilities

    Implementing batch URL processing

    Adding authentication support

    Creating data visualization of scraped results
```
This gives you a complete, working Beautiful Soup scraper with a nice UI! Want me to help you with the next project (Scrapy/Selenium) or add any features to this one?
