# app_basic.py
# This is a simplified version to test if everything works

import streamlit as st
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import re
import matplotlib.pyplot as plt
import ssl

# Download NLTK data (only first time)
def download_nltk_data():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('wordnet', quiet=True)

download_nltk_data()

st.set_page_config(page_title="📚 Book Analyzer - Basic", page_icon="📚")

st.title("📚 Book Text Analyzer - Basic Version")
st.write("Testing if everything works...")

# Upload file
uploaded_file = st.file_uploader("Upload a text file (.txt)", type=['txt'])

if uploaded_file:
    # Read the file
    text = uploaded_file.read().decode('utf-8')
    
    # Show basic stats
    st.subheader("📊 Basic Statistics")
    col1, col2 = st.columns(2)
    col1.metric("Total Characters", len(text))
    col2.metric("Total Words", len(text.split()))
    
    # Preprocess text
    clean_text = text.lower()
    clean_text = re.sub("[^a-zA-Z0-9]", " ", clean_text)
    
    # Tokenize
    tokens = word_tokenize(clean_text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    tokens = [word for word in tokens if len(word) >= 3]
    
    st.write(f"Number of tokens after cleaning: {len(tokens)}")
    
    # Show most common words
    fdist = nltk.FreqDist(tokens)
    st.subheader("🏆 Top 10 Words")
    st.write(fdist.most_common(10))
    
    # Sentiment Analysis
    st.subheader("😊 Sentiment Analysis")
    analyzer = SentimentIntensityAnalyzer()
    
    # Split into sentences (simplified)
    sentences = text.split('.')
    sentences = [s.strip() for s in sentences if len(s) > 10]
    
    # Analyze first 10 sentences
    sentiments = []
    for s in sentences[:10]:
        scores = analyzer.polarity_scores(s)
        sentiments.append(scores['compound'])
    
    st.write(f"Average sentiment: {sum(sentiments)/len(sentiments):.2f}")
    st.write(f"Range: {min(sentiments):.2f} to {max(sentiments):.2f}")
    
    # Show sentiment distribution
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.hist(sentiments, bins=20, color='steelblue')
    ax.set_title('Sentiment Distribution (First 10 sentences)')
    st.pyplot(fig)
    plt.close()
    
    # Word Cloud
    st.subheader("☁️ Word Cloud")
    wordcloud = WordCloud(max_words=100, background_color='white').generate(clean_text)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis('off')
    st.pyplot(fig)
    plt.close()

else:
    st.info("👈 Please upload a .txt file to begin analysis")

st.write("---")
st.write("✅ Basic version working! Now we can add more features.")