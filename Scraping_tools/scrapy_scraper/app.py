from flask import Flask, render_template, request, jsonify, send_file
from scrapy_runner import ScrapyRunner
import json
import csv
import io
from datetime import datetime
import os

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

runner = ScrapyRunner()
scrape_results = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    global scrape_results
    try:
        data = request.get_json()
        url = data.get('url')
        selector = data.get('selector')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        result = runner.scrape_single(url, selector)
        
        if result:
            scrape_results = [result]
            return jsonify(result)
        else:
            return jsonify({'error': 'No data scraped'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape/batch', methods=['POST'])
def scrape_batch():
    global scrape_results
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        selector = data.get('selector', '')
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        results = []
        for url in urls:
            if url.strip():
                result = runner.scrape_single(url.strip(), selector)
                if result:
                    results.append(result)
        
        scrape_results = results
        return jsonify({
            'total': len(results),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
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
    app.run(debug=True, host='0.0.0.0', port=5001)
