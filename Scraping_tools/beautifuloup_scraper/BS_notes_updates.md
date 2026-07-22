💡 Next Steps

Once this works, you can extend it by:

    Adding download functionality (CSV/JSON export)

    Adding scheduling capabilities

    Implementing batch URL processing

    Adding authentication support

    Creating data visualization of scraped results

Excellent! Glad the first version is working. Let's add the most useful features next. I recommend starting with CSV/JSON export and batch URL processing since they add immediate practical value.
🚀 Feature 1: Export to CSV/JSON
Update app.py to add export endpoints:
python

from flask import Flask, render_template, request, jsonify, send_file
from scraper import BeautifulSoupScraper
import json
import csv
import io
from datetime import datetime

app = Flask(__name__)
scraper = BeautifulSoupScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        url = data.get('url')
        selector = data.get('selector')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = scraper.scrape_website(url, selector)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/batch', methods=['POST'])
def scrape_batch():
    """Scrape multiple URLs at once"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        selector = data.get('selector', '')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        results = []
        for url in urls:
            if url.strip():
                result = scraper.scrape_website(url.strip(), selector)
                results.append(result)
        
        return jsonify({
            'total': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export scraped data to CSV"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['URL', 'Title', 'Data', 'Timestamp'])
        
        # Write rows
        for item in scraped_data:
            writer.writerow([
                item.get('url', ''),
                item.get('title', ''),
                ' | '.join(item.get('data', [])[:5]),  # Limit to first 5 items
                datetime.now().isoformat()
            ])
        
        # Create response
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
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Create JSON in memory
        output = io.StringIO()
        json.dump({
            'export_date': datetime.now().isoformat(),
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
    app.run(debug=True, host='0.0.0.0', port=5000)

📊 Feature 2: Enhanced Frontend with Export & Batch

Update your templates/index.html:
html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beautiful Soup Scraper Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        .scraped-data {
            max-height: 400px;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
        }
        .batch-url-input {
            min-height: 100px;
        }
        .loading {
            display: none;
        }
        .result-item {
            border-left: 4px solid #0d6efd;
            padding-left: 15px;
            margin-bottom: 10px;
        }
        .export-buttons .btn {
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-md-10 mx-auto">
                <h1 class="text-primary mb-4">
                    <i class="bi bi-file-code"></i> 
                    Beautiful Soup Scraper
                    <small class="text-muted fs-6">with Export & Batch Processing</small>
                </h1>

                <!-- Mode Selection -->
                <div class="btn-group w-100 mb-4" role="group">
                    <input type="radio" class="btn-check" name="mode" id="singleMode" value="single" checked>
                    <label class="btn btn-outline-primary" for="singleMode">
                        <i class="bi bi-file-earmark"></i> Single URL
                    </label>
                    <input type="radio" class="btn-check" name="mode" id="batchMode" value="batch">
                    <label class="btn btn-outline-primary" for="batchMode">
                        <i class="bi bi-files"></i> Batch URLs
                    </label>
                </div>

                <!-- Single URL Mode -->
                <div id="singleModeContent" class="card shadow mb-4">
                    <div class="card-body">
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

                        <div class="mb-3">
                            <label for="selector" class="form-label">CSS Selector (optional)</label>
                            <input type="text" class="form-control" id="selector" 
                                   placeholder=".main-content, #title, .product-item">
                        </div>

                        <button class="btn btn-success btn-lg w-100" id="scrapeBtn">
                            <i class="bi bi-play-circle"></i> Scrape Now
                        </button>
                    </div>
                </div>

                <!-- Batch Mode -->
                <div id="batchModeContent" class="card shadow mb-4" style="display: none;">
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="batchUrls" class="form-label">Enter URLs (one per line)</label>
                            <textarea class="form-control batch-url-input" id="batchUrls" 
                                      placeholder="https://example.com
https://example.org
https://example.net"></textarea>
                        </div>

                        <div class="mb-3">
                            <label for="batchSelector" class="form-label">CSS Selector (optional)</label>
                            <input type="text" class="form-control" id="batchSelector" 
                                   placeholder=".main-content, #title">
                        </div>

                        <button class="btn btn-primary btn-lg w-100" id="batchScrapeBtn">
                            <i class="bi bi-play-circle"></i> Scrape All URLs
                        </button>
                    </div>
                </div>

                <!-- Results Section -->
                <div id="resultContainer" style="display: none;">
                    <div class="card shadow">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0"><i class="bi bi-file-text"></i> Scraped Data</h5>
                            <div class="export-buttons">
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
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Scraping in progress...</p>
                            </div>
                            <div id="resultContent"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Toggle between single and batch mode
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', function() {
                document.getElementById('singleModeContent').style.display = 
                    this.value === 'single' ? 'block' : 'none';
                document.getElementById('batchModeContent').style.display = 
                    this.value === 'batch' ? 'block' : 'none';
            });
        });

        // Store scraped data for export
        let scrapedData = [];

        // Preview functionality (single)
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

        // Single scrape
        document.getElementById('scrapeBtn').addEventListener('click', async function() {
            const url = document.getElementById('url').value;
            const selector = document.getElementById('selector').value;
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }

            await performScrape([{url, selector}], 'Single URL');
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
            const scrapeTasks = urls.map(url => ({url: url.trim(), selector}));
            
            await performScrape(scrapeTasks, `Batch (${urls.length} URLs)`);
        });

        // Core scrape function
        async function performScrape(tasks, label) {
            const resultContainer = document.getElementById('resultContainer');
            const loadingIndicator = document.getElementById('loadingIndicator');
            const resultContent = document.getElementById('resultContent');
            
            resultContainer.style.display = 'block';
            loadingIndicator.style.display = 'block';
            resultContent.innerHTML = '';
            document.querySelectorAll('button:not(.btn-outline-secondary):not(.btn-secondary)').forEach(btn => 
                btn.disabled = true
            );

            try {
                if (tasks.length === 1) {
                    // Single scrape
                    const response = await fetch('/scrape', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            url: tasks[0].url,
                            selector: tasks[0].selector
                        })
                    });
                    const data = await response.json();
                    scrapedData = [data];
                    displayResults([data], label);
                } else {
                    // Batch scrape
                    const response = await fetch('/scrape/batch', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            urls: tasks.map(t => t.url),
                            selector: tasks[0].selector
                        })
                    });
                    const data = await response.json();
                    scrapedData = data.results || [];
                    displayResults(scrapedData, label);
                }
            } catch (error) {
                resultContent.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-x-circle"></i> ${error.message}
                    </div>
                `;
            } finally {
                loadingIndicator.style.display = 'none';
                document.querySelectorAll('button:not(.btn-outline-secondary):not(.btn-secondary)').forEach(btn => 
                    btn.disabled = false
                );
            }
        }

        // Display results
        function displayResults(data, label) {
            const resultContent = document.getElementById('resultContent');
            
            if (!data || data.length === 0 || data[0]?.error) {
                resultContent.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle"></i> 
                        ${data[0]?.error || 'No data found'}
                    </div>
                `;
                return;
            }

            let html = `
                <div class="alert alert-info">
                    <i class="bi bi-info-circle"></i> 
                    ${label} - Found ${data.length} result(s)
                    <span class="badge bg-primary ms-2">${new Date().toLocaleTimeString()}</span>
                </div>
            `;

            data.forEach((item, index) => {
                if (item.error) {
                    html += `
                        <div class="alert alert-danger result-item">
                            <strong>${item.url}</strong><br>
                            ⚠️ ${item.error}
                        </div>
                    `;
                } else {
                    html += `
                        <div class="result-item">
                            <strong>${index + 1}. ${item.title || 'No title'}</strong>
                            <span class="badge bg-success ms-2">${item.status_code}</span>
                            <span class="badge bg-info ms-2">${item.count || 0} items</span>
                            <br>
                            <small class="text-muted">${item.url}</small>
                            <div class="mt-2">
                                <pre class="bg-light p-2 rounded" style="max-height: 150px; overflow-y: auto;">${JSON.stringify(item.data, null, 2)}</pre>
                            </div>
                        </div>
                    `;
                }
            });

            resultContent.innerHTML = html;
        }

        // Export to CSV
        document.getElementById('exportCsvBtn').addEventListener('click', async function() {
            if (scrapedData.length === 0) {
                alert('No data to export. Scrape something first!');
                return;
            }

            try {
                const response = await fetch('/export/csv', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        data: scrapedData,
                        filename: `scrape_${new Date().toISOString().slice(0,10)}`
                    })
                });
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrape_${new Date().toISOString().slice(0,10)}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
            } catch (error) {
                alert('Export failed: ' + error.message);
            }
        });

        // Export to JSON
        document.getElementById('exportJsonBtn').addEventListener('click', async function() {
            if (scrapedData.length === 0) {
                alert('No data to export. Scrape something first!');
                return;
            }

            try {
                const response = await fetch('/export/json', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        data: scrapedData,
                        filename: `scrape_${new Date().toISOString().slice(0,10)}`
                    })
                });
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrape_${new Date().toISOString().slice(0,10)}.json`;
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

🧪 Test the New Features

    Single Scrape + Export:

        Scrape https://news.ycombinator.com with selector .titleline

        Click CSV or JSON to download

    Batch Processing:

        Switch to "Batch URLs" mode

        Enter multiple URLs:
        text

        https://example.com
        https://example.org
        https://example.net

        Click "Scrape All URLs"

    Export Options:

        CSV: Good for Excel/spreadsheets

        JSON: Good for APIs/programming

🎯 Next Features to Add

Once this is working, we can add:
1. Scheduling (with APScheduler):
python

from apscheduler.schedulers.background import BackgroundScheduler

# Add scheduled scraping
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_daily, trigger="cron", hour=9)
scheduler.start()

2. Authentication Support:

    Basic Auth

    Session-based login

    OAuth2

3. Data Visualization:

    Charts for scraped data

    Word clouds

    Statistics dashboard

4. Webhook Integration:

    Send results to Slack/Telegram

    Email notifications

📦 Install Additional Dependencies (for future features)
bash

pip install apscheduler  # For scheduling
pip install pandas       # For data manipulation
pip install matplotlib   # For charts

Which feature would you like to add next? I'd recommend:

    Scheduling if you want automated scraping

    Authentication if you need to scrape protected content

    Data Visualization if you want to analyze results visually

Let me know and I'll guide you through implementing it! 🚀


🔧 Fix 1: Add the Preview Endpoint

Add this to your app.py:
python

@app.route('/preview', methods=['POST'])
def preview():
    """Preview a website without full scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Just get the title and basic info
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        return jsonify({
            'title': soup.title.string if soup.title else 'No title',
            'status': response.status_code,
            'content_type': response.headers.get('content-type', 'unknown')
        })
    
    except requests.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

🔧 Fix 2: Add Bootstrap JavaScript for Dropdowns

The dropdown menu isn't opening because you're missing Bootstrap's JavaScript bundle. Add this to your index.html before the closing </body> tag:
html

<!-- Bootstrap JS Bundle with Popper -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

🔧 Fix 3: Complete Updated app.py

Here's your complete app.py with all endpoints:
python

from flask import Flask, render_template, request, jsonify, send_file
from scraper import BeautifulSoupScraper
import json
import csv
import io
from datetime import datetime

app = Flask(__name__)
scraper = BeautifulSoupScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/preview', methods=['POST'])
def preview():
    """Preview a website without full scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        return jsonify({
            'title': soup.title.string if soup.title else 'No title',
            'status': response.status_code,
            'content_type': response.headers.get('content-type', 'unknown')
        })
    
    except requests.RequestException as e:
        return jsonify({'error': f'Request failed: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle single URL scraping"""
    try:
        data = request.get_json()
        url = data.get('url')
        selector = data.get('selector')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = scraper.scrape_website(url, selector)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/batch', methods=['POST'])
def scrape_batch():
    """Scrape multiple URLs at once"""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        selector = data.get('selector', '')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        results = []
        for url in urls:
            if url.strip():
                result = scraper.scrape_website(url.strip(), selector)
                results.append(result)
        
        return jsonify({
            'total': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    """Export scraped data to CSV (Summary)"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['URL', 'Title', 'Status', 'Item Count', 'Data Preview', 'Timestamp'])
        
        # Write rows
        for item in scraped_data:
            data_items = item.get('data', [])
            
            if isinstance(data_items, list):
                data_preview = ' | '.join(str(item)[:100] for item in data_items[:3])
                if len(data_items) > 3:
                    data_preview += '...'
            else:
                data_preview = str(data_items)[:300]
            
            writer.writerow([
                item.get('url', ''),
                item.get('title', 'No title'),
                item.get('status_code', 'N/A'),
                item.get('count', len(data_items) if isinstance(data_items, list) else 0),
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

@app.route('/export/csv/detailed', methods=['POST'])
def export_csv_detailed():
    """Export scraped data to CSV (One row per item)"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['URL', 'Title', 'Item_Number', 'Data_Item', 'Timestamp'])
        
        for item in scraped_data:
            data_items = item.get('data', [])
            
            if isinstance(data_items, list) and data_items:
                for idx, data_item in enumerate(data_items, 1):
                    writer.writerow([
                        item.get('url', ''),
                        item.get('title', 'No title'),
                        idx,
                        str(data_item)[:500],
                        datetime.now().isoformat()
                    ])
            else:
                writer.writerow([
                    item.get('url', ''),
                    item.get('title', 'No title'),
                    0,
                    str(data_items)[:500] if data_items else 'No data',
                    datetime.now().isoformat()
                ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}_detailed.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/json', methods=['POST'])
def export_json():
    """Export scraped data to JSON"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        json.dump({
            'export_date': datetime.now().isoformat(),
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

@app.route('/export/txt', methods=['POST'])
def export_txt():
    """Export scraped data to plain text"""
    try:
        data = request.get_json()
        scraped_data = data.get('data', [])
        filename = data.get('filename', f'scraped_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not scraped_data:
            return jsonify({'error': 'No data to export'}), 400
        
        output = io.StringIO()
        output.write(f"Scraped Data Export - {datetime.now().isoformat()}\n")
        output.write("=" * 60 + "\n\n")
        
        for idx, item in enumerate(scraped_data, 1):
            output.write(f"{idx}. URL: {item.get('url', 'N/A')}\n")
            output.write(f"   Title: {item.get('title', 'No title')}\n")
            output.write(f"   Status: {item.get('status_code', 'N/A')}\n")
            output.write(f"   Items: {item.get('count', 0)}\n")
            output.write("   Data:\n")
            
            data_items = item.get('data', [])
            if isinstance(data_items, list):
                for data_idx, data_item in enumerate(data_items[:10], 1):
                    output.write(f"     {data_idx}. {str(data_item)[:200]}\n")
                if len(data_items) > 10:
                    output.write(f"     ... and {len(data_items) - 10} more items\n")
            else:
                output.write(f"     {str(data_items)[:500]}\n")
            
            output.write("\n" + "-" * 40 + "\n\n")
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'{filename}.txt'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

🔧 Fix 4: Update HTML - Add Bootstrap JS

At the end of your templates/index.html, make sure you have:
html

<!-- Bootstrap JS Bundle with Popper - Required for dropdowns -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

<!-- Your custom JavaScript -->
<script>
    // ... all your JavaScript code ...
</script>
</body>
</html>

🔧 Fix 5: Simplified Export Buttons (if dropdown still not working)

If the dropdown still doesn't work, use a simpler button group approach:
html

<div class="export-buttons">
    <button class="btn btn-sm btn-success" id="exportCsvBtn">
        <i class="bi bi-file-earmark-excel"></i> CSV
    </button>
    <button class="btn btn-sm btn-info" id="exportJsonBtn">
        <i class="bi bi-file-earmark-code"></i> JSON
    </button>
    <button class="btn btn-sm btn-secondary" id="exportTxtBtn">
        <i class="bi bi-file-earmark-text"></i> TXT
    </button>
    <button class="btn btn-sm btn-secondary" id="clearResultsBtn">
        <i class="bi bi-x-circle"></i> Clear
    </button>
</div>

And add the event listeners for these buttons.
🧪 Restart and Test

    Restart your Flask app:
    bash

    # Stop the current server (Ctrl+C)
    python app.py

    Test the preview:

        Enter a URL

        Click "Preview"

        Should show title and status

    Test scraping:

        Enter https://news.ycombinator.com

        Selector: .titleline

        Click "Scrape Now"

    Test export:

        Click CSV button

        File should download