# flask_app.py
from flask import Flask, render_template, request, jsonify
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
import pandas as pd
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get text from request
    text = request.form.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'})
    
    # Perform analysis
    results = {
        'word_count': len(text.split()),
        'char_count': len(text),
        'sentences': len(text.split('.')),
    }
    
    # Sentiment analysis
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    results['sentiment'] = sentiment
    
    # Word frequency
    clean_text = re.sub("[^a-zA-Z0-9]", " ", text.lower())
    tokens = clean_text.split()
    tokens = [w for w in tokens if w not in stopwords.words('english') and len(w) >= 3]
    
    freq = nltk.FreqDist(tokens)
    results['common_words'] = freq.most_common(20)
    
    # Generate word cloud as base64 image
    wordcloud = WordCloud(max_words=200, background_color='white').generate(text)
    
    img = io.BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    results['wordcloud'] = base64.b64encode(img.getvalue()).decode()
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)