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