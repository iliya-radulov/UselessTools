# 🚀 Let's Build Scrapy Project
## Project 2: Scrapy Web Scraper with Flask UI

```text
We'll build a separate Flask app that uses Scrapy as the backend engine.
📦 Installation
```

```bash
# Create new project folder
mkdir scrapy_scraper
cd scrapy_scraper
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
# Install dependencies
pip install Flask scrapy twisted python-dotenv
```
```text
📋 requirements.txt
txt

Flask==2.3.2
Scrapy==2.11.2
twisted==24.3.0
python-dotenv==1.0.0
```
🕷️ Create Scrapy Project

```bash
# Create Scrapy project structure
scrapy startproject scrapy_project

# Your structure will be:
# scrapy_project/
#   ├── scrapy_project/
#   │   ├── spiders/
#   │   │   └── __init__.py
#   │   ├── __init__.py
#   │   ├── items.py
#   │   ├── middlewares.py
#   │   ├── pipelines.py
#   │   └── settings.py
#   └── scrapy.cfg
```

 
# Create a Spider

Create scrapy_project/spiders/generic_spider.py:
 
```python

import scrapy
from scrapy.selector import Selector
from scrapy.http import HtmlResponse
import json

class GenericSpider(scrapy.Spider):
    name = 'generic'
    
    def __init__(self, url=None, selector=None, *args, **kwargs):
        super(GenericSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url] if url else []
        self.selector = selector or ''
        self.results = []
    
    def parse(self, response):
        """Parse the response and extract data"""
        items = []
        
        if self.selector:
            # Use CSS selector
            elements = response.css(self.selector)
            for elem in elements:
                items.append({
                    'text': elem.css('::text').get(default='').strip(),
                    'html': elem.get()
                })
        else:
            # Get all text
            text = response.css('body::text').getall()
            items.append({
                'text': ' '.join(text)[:1000],  # Limit to 1000 chars
                'html': response.text[:1000] if len(response.text) > 1000 else response.text
            })
        
        # Store results
        self.results.append({
            'url': response.url,
            'status': response.status,
            'title': response.css('title::text').get(default='No title'),
            'count': len(items),
            'data': items[:50]  # Limit to 50 items
        })
        
        return items
    
    def closed(self, reason):
        """Called when spider closes"""
        self.logger.info(f'Spider closed: {reason}')
```

# 🧠 Scrapy Runner Utility

Create scrapy_runner.py in the project root:
```python

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import json
import os
from datetime import datetime

class ScrapyRunner:
    def __init__(self):
        # Set up Scrapy settings
        self.settings = get_project_settings()
        self.settings.set('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.settings.set('ROBOTSTXT_OBEY', False)
        self.settings.set('LOG_LEVEL', 'INFO')
        
    def scrape_single(self, url, selector=None):
        """Run Scrapy spider for a single URL"""
        from scrapy_project.spiders.generic_spider import GenericSpider
        
        # Create a crawler process
        process = CrawlerProcess(self.settings)
        
        # Create spider with parameters
        spider = GenericSpider(url=url, selector=selector)
        
        # Crawl
        process.crawl(spider)
        process.start()  # This blocks until complete
        
        # Get results
        results = spider.results
        process.stop()
        
        return results[0] if results else None
    
    def scrape_batch(self, urls, selector=None):
        """Run Scrapy spider for multiple URLs"""
        from scrapy_project.spiders.generic_spider import GenericSpider
        
        process = CrawlerProcess(self.settings)
        
        all_results = []
        for url in urls:
            if url.strip():
                spider = GenericSpider(url=url.strip(), selector=selector)
                process.crawl(spider)
        
        process.start()  # This will crawl all spiders
        
        # Collect results from all spiders
        # Note: This simplified version runs sequentially
        # For true concurrency, we need a different approach
        
        return all_results

# Alternative: Async version using CrawlerRunner
from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging

class AsyncScrapyRunner:
    def __init__(self):
        configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
        self.runner = CrawlerRunner(get_project_settings())
        self.results = []
    
    @defer.inlineCallbacks
    def scrape_single_async(self, url, selector=None):
        """Async scraping for use with Flask"""
        from scrapy_project.spiders.generic_spider import GenericSpider
        
        spider = GenericSpider(url=url, selector=selector)
        yield self.runner.crawl(spider)
        
        # Results are stored in spider
        result = spider.results[0] if spider.results else None
        self.results.append(result)
        
        return result

🌐 Flask App for Scrapy

Create app.py:
python

from flask import Flask, render_template, request, jsonify, send_file
from scrapy_runner import ScrapyRunner
import json
import csv
import io
from datetime import datetime
import threading
import time

app = Flask(__name__)
runner = ScrapyRunner()

# Store results and job status
scrape_results = []
scrape_status = {
    'status': 'idle',
    'progress': 0,
    'total': 0,
    'current_url': ''
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Single URL scrape using Scrapy"""
    global scrape_results, scrape_status
    
    try:
        data = request.get_json()
        url = data.get('url')
        selector = data.get('selector')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Update status
        scrape_status = {
            'status': 'running',
            'progress': 1,
            'total': 1,
            'current_url': url
        }
        
        # Run Scrapy
        result = runner.scrape_single(url, selector)
        
        if result:
            scrape_results = [result]
            scrape_status['status'] = 'complete'
            return jsonify(result)
        else:
            scrape_status['status'] = 'error'
            return jsonify({'error': 'No data scraped'}), 500
            
    except Exception as e:
        scrape_status['status'] = 'error'
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/batch', methods=['POST'])
def scrape_batch():
    """Batch URL scrape using Scrapy"""
    global scrape_results, scrape_status
    
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        selector = data.get('selector', '')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        # Update status
        scrape_status = {
            'status': 'running',
            'progress': 0,
            'total': len(urls),
            'current_url': ''
        }
        
        results = []
        for idx, url in enumerate(urls):
            if url.strip():
                scrape_status['current_url'] = url.strip()
                result = runner.scrape_single(url.strip(), selector)
                if result:
                    results.append(result)
                scrape_status['progress'] = idx + 1
        
        scrape_results = results
        scrape_status['status'] = 'complete'
        
        return jsonify({
            'total': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        scrape_status['status'] = 'error'
        return jsonify({'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current scraping status"""
    return jsonify(scrape_status)

# Export endpoints (similar to BeautifulSoup version)
@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export scraped data to CSV"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scrapy_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['URL', 'Title', 'Status', 'Item Count', 'Data Preview', 'Timestamp'])
        
        for item in scraped_data:
            data_items = item.get('data', [])
            data_preview = ' | '.join([d.get('text', '')[:50] for d in data_items[:3]])
            if len(data_items) > 3:
                data_preview += '...'
            
            writer.writerow([
                item.get('url', ''),
                item.get('title', 'No title'),
                item.get('status', 'N/A'),
                item.get('count', 0),
                data_preview,
                datetime.now().isoformat()
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/json', methods=['POST'])
def export_json():
    """Export scraped data to JSON"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scrapy_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        json.dump({
            'export_date': datetime.now().isoformat(),
            'tool': 'Scrapy',
            'total_items': len(scraped_data),
            'data': scraped_data
        }, output, indent=2)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'{filename}.json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Different port!
```

# 🎨 Create Templates

Create templates/index.html:

```html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scrapy Scraper</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        .status-badge {
            font-size: 1rem;
            padding: 8px 15px;
        }
        .progress-bar {
            transition: width 0.5s;
        }
        .result-item {
            border-left: 4px solid #0d6efd;
            padding-left: 15px;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-10 mx-auto">
                <h1 class="text-success mb-4">
                    <i class="bi bi-spider"></i> 
                    Scrapy Scraper
                    <small class="text-muted fs-6">High-performance web scraping</small>
                </h1>

                <!-- Status Bar -->
                <div id="statusBar" class="alert alert-info mb-4" style="display: none;">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="bi bi-info-circle"></i>
                            <span id="statusText">Idle</span>
                        </div>
                        <div>
                            <span id="progressText" class="badge bg-primary">0/0</span>
                        </div>
                    </div>
                    <div class="progress mt-2" style="height: 10px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             id="progressBar" style="width: 0%"></div>
                    </div>
                </div>

                <!-- URL Input -->
                <div class="card shadow mb-4">
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="url" class="form-label">Website URL</label>
                            <input type="url" class="form-control" id="url" 
                                   placeholder="https://example.com" 
                                   value="https://example.com">
                        </div>

                        <div class="mb-3">
                            <label for="selector" class="form-label">CSS Selector (optional)</label>
                            <input type="text" class="form-control" id="selector" 
                                   placeholder=".main-content, #title, .product-item">
                        </div>

                        <button class="btn btn-success btn-lg w-100" id="scrapeBtn">
                            <i class="bi bi-play-circle"></i> Scrape with Scrapy
                        </button>
                    </div>
                </div>

                <!-- Batch Mode -->
                <div class="card shadow mb-4">
                    <div class="card-header">
                        <h5><i class="bi bi-files"></i> Batch Mode</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="batchUrls" class="form-label">Enter URLs (one per line)</label>
                            <textarea class="form-control" id="batchUrls" rows="4" 
                                      placeholder="https://example.com
https://example.org
https://example.net"></textarea>
                        </div>
                        <div class="mb-3">
                            <label for="batchSelector" class="form-label">CSS Selector (optional)</label>
                            <input type="text" class="form-control" id="batchSelector" 
                                   placeholder=".main-content">
                        </div>
                        <button class="btn btn-primary w-100" id="batchScrapeBtn">
                            <i class="bi bi-play-circle"></i> Scrape All URLs
                        </button>
                    </div>
                </div>

                <!-- Results -->
                <div id="resultContainer" style="display: none;">
                    <div class="card shadow">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0"><i class="bi bi-file-text"></i> Scraped Data</h5>
                            <div>
                                <button class="btn btn-sm btn-success" id="exportCsvBtn">
                                    <i class="bi bi-file-earmark-excel"></i> CSV
                                </button>
                                <button class="btn btn-sm btn-info" id="exportJsonBtn">
                                    <i class="bi bi-file-earmark-code"></i> JSON
                                </button>
                                <button class="btn btn-sm btn-secondary" id="clearResultsBtn">
                                    <i class="bi bi-x-circle"></i> Clear
                                </button>
                            </div>
                        </div>
                        <div class="card-body">
                            <div id="loadingIndicator" class="text-center py-4" style="display: none;">
                                <div class="spinner-border text-success" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Scrapy is crawling...</p>
                                <small class="text-muted" id="currentUrl">Starting...</small>
                            </div>
                            <div id="resultContent"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let scrapedData = [];
        let statusInterval;

        // Check status periodically during scraping
        function checkStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const statusBar = document.getElementById('statusBar');
                    const statusText = document.getElementById('statusText');
                    const progressBar = document.getElementById('progressBar');
                    const progressText = document.getElementById('progressText');
                    
                    statusBar.style.display = 'block';
                    
                    if (data.status === 'running') {
                        statusText.innerHTML = '<span class="text-warning">⏳ Scraping...</span>';
                        const progress = data.total > 0 ? (data.progress / data.total * 100) : 0;
                        progressBar.style.width = progress + '%';
                        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
                        progressText.textContent = `${data.progress}/${data.total}`;
                        document.getElementById('currentUrl').textContent = `Current: ${data.current_url || 'Starting...'}`;
                    } else if (data.status === 'complete') {
                        statusText.innerHTML = '<span class="text-success">✅ Complete!</span>';
                        progressBar.style.width = '100%';
                        progressBar.className = 'progress-bar bg-success';
                        clearInterval(statusInterval);
                    } else if (data.status === 'error') {
                        statusText.innerHTML = '<span class="text-danger">❌ Error</span>';
                        clearInterval(statusInterval);
                    }
                })
                .catch(error => console.error('Status check failed:', error));
        }

        // Show results
        function displayResults(data) {
            const resultContainer = document.getElementById('resultContainer');
            const resultContent = document.getElementById('resultContent');
            
            resultContainer.style.display = 'block';
            resultContent.innerHTML = '';
            
            if (!data || data.length === 0) {
                resultContent.innerHTML = '<div class="alert alert-warning">No data found</div>';
                return;
            }

            let html = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> 
                    Scrapy found ${data.length} result(s)
                    <span class="badge bg-success ms-2">${new Date().toLocaleTimeString()}</span>
                </div>
            `;

            data.forEach((item, index) => {
                html += `
                    <div class="result-item">
                        <strong>${index + 1}. ${item.title || 'No title'}</strong>
                        <span class="badge bg-success ms-2">${item.status}</span>
                        <span class="badge bg-info ms-2">${item.count || 0} items</span>
                        <br>
                        <small class="text-muted">${item.url}</small>
                        <div class="mt-2">
                            <pre class="bg-light p-2 rounded" style="max-height: 150px; overflow-y: auto;">${JSON.stringify(item.data?.slice(0, 3) || 'No data', null, 2)}</pre>
                        </div>
                    </div>
                `;
            });

            resultContent.innerHTML = html;
            scrapedData = data;
        }

        // Scrape single URL
        document.getElementById('scrapeBtn').addEventListener('click', async function() {
            const url = document.getElementById('url').value;
            const selector = document.getElementById('selector').value;
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            // Show loading
            document.getElementById('resultContainer').style.display = 'block';
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('resultContent').innerHTML = '';
            this.disabled = true;

            // Start status checking
            statusInterval = setInterval(checkStatus, 1000);

            try {
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url, selector})
                });
                
                const data = await response.json();
                
                document.getElementById('loadingIndicator').style.display = 'none';
                
                if (data.error) {
                    document.getElementById('resultContent').innerHTML = 
                        `<div class="alert alert-danger">${data.error}</div>`;
                } else {
                    displayResults([data]);
                }
            } catch (error) {
                document.getElementById('loadingIndicator').style.display = 'none';
                document.getElementById('resultContent').innerHTML = 
                    `<div class="alert alert-danger">${error.message}</div>`;
            } finally {
                this.disabled = false;
                clearInterval(statusInterval);
            }
        });

        // Batch scrape
        document.getElementById('batchScrapeBtn').addEventListener('click', async function() {
            const urlsText = document.getElementById('batchUrls').value;
            const selector = document.getElementById('batchSelector').value;
            
            if (!urlsText) {
                alert('Please enter at least one URL');
                return;
            }

            const urls = urlsText.split('\n').filter(url => url.trim());
            
            document.getElementById('resultContainer').style.display = 'block';
            document.getElementById('loadingIndicator').style.display = 'block';
            document.getElementById('resultContent').innerHTML = '';
            this.disabled = true;

            statusInterval = setInterval(checkStatus, 1000);

            try {
                const response = await fetch('/scrape/batch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        urls: urls,
                        selector: selector
                    })
                });
                
                const data = await response.json();
                
                document.getElementById('loadingIndicator').style.display = 'none';
                
                if (data.error) {
                    document.getElementById('resultContent').innerHTML = 
                        `<div class="alert alert-danger">${data.error}</div>`;
                } else {
                    displayResults(data.results || []);
                }
            } catch (error) {
                document.getElementById('loadingIndicator').style.display = 'none';
                document.getElementById('resultContent').innerHTML = 
                    `<div class="alert alert-danger">${error.message}</div>`;
            } finally {
                this.disabled = false;
                clearInterval(statusInterval);
            }
        });

        // Export CSV
        document.getElementById('exportCsvBtn').addEventListener('click', async function() {
            if (scrapedData.length === 0) {
                alert('No data to export. Scrape something first!');
                return;
            }

            try {
                const response = await fetch('/export/csv', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({data: scrapedData})
                });
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrapy_export_${new Date().toISOString().slice(0,10)}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Export failed: ' + error.message);
            }
        });

        // Export JSON
        document.getElementById('exportJsonBtn').addEventListener('click', async function() {
            if (scrapedData.length === 0) {
                alert('No data to export. Scrape something first!');
                return;
            }

            try {
                const response = await fetch('/export/json', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({data: scrapedData})
                });
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrapy_export_${new Date().toISOString().slice(0,10)}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Export failed: ' + error.message);
            }
        });

        // Clear results
        document.getElementById('clearResultsBtn').addEventListener('click', function() {
            document.getElementById('resultContainer').style.display = 'none';
            document.getElementById('resultContent').innerHTML = '';
            scrapedData = [];
        });
    </script>
</body>
</html>
```

# 🚀 Run the Scrapy App

```bash
# In the scrapy_scraper directory
python app.py
# Access at: http://localhost:5001
```

🆚 Comparison: Beautiful Soup vs Scrapy
Feature	Beautiful Soup	Scrapy
Speed	Slower (single-threaded)	Much faster (async/concurrent)
Use Case	Simple, small projects	Large-scale, production
Setup	Simple library	Full framework
Learning Curve	Easy	Steep
Built-in Features	Minimal	Pipelines, exporters, middlewares
JavaScript	No	No (needs Splash/Playwright)
Best For	Quick scripts	Professional scraping projects
📊 Project Status
text

✅ Beautiful Soup App - Complete (Port 5000)
🔄 Scrapy App - Starting (Port 5001)
⏳ Selenium App - Future
⏳ Octoparse App - Future

🎯 Next Steps

    Run the Scrapy app and test it

    Compare results with Beautiful Soup

    Then we'll build Selenium for dynamic content

Ready to start Scrapy? Run the code and let me know if you hit any issues! 🚀
