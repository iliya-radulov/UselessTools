I'll help you build a text/book analyzer web app based on your Jupyter notebooks. HTML alone won't work since you need Python for the actual analysis. Here are the best options:
Best Option: Streamlit Web App

Streamlit is perfect for this - it's Python-based, easy to deploy, and works great for data apps.

```python

# app.py
import streamlit as st
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from gensim.corpora import Dictionary
from gensim.models import ldamodel
from gensim.models.coherencemodel import CoherenceModel
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import ssl
import tempfile
import os

# Download NLTK data
@st.cache_resource
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

# Cache the text processing functions
@st.cache_data
def load_text(uploaded_file):
    text = uploaded_file.read().decode('utf-8')
    return text

@st.cache_data
def preprocess_text(text):
    # Lowercase and clean
    word_cloud_text = text.lower()
    word_cloud_text = re.sub("[^a-zA-Z0-9]", " ", word_cloud_text)
    return word_cloud_text

@st.cache_data
def tokenize_text(text):
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    tokens = [word for word in tokens if len(word) >= 3]
    return tokens

@st.cache_data
def split_sentences(text):
    alphabets = "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\\s|She\\s|It\\s|They\\s|Their\\s|Our\\s|We\\s|But\\s|However\\s|That\\s|This\\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov|edu|me)"
    digits = "([0-9])"
    
    processed_text = " " + text + "  "
    processed_text = processed_text.replace("\n", " ")
    processed_text = re.sub(prefixes, "\\1<prd>", processed_text)
    processed_text = re.sub(websites, "<prd>\\1", processed_text)
    processed_text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", processed_text)
    
    if "..." in processed_text:
        processed_text = processed_text.replace("...", "<prd><prd><prd>")
    if "Ph.D" in processed_text:
        processed_text = processed_text.replace("Ph.D.", "Ph<prd>D<prd>")
    
    processed_text = re.sub("\\s" + alphabets + "[.] ", " \\1<prd> ", processed_text)
    processed_text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", processed_text)
    processed_text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", processed_text)
    processed_text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", processed_text)
    processed_text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", processed_text)
    processed_text = re.sub(" " + suffixes + "[.]", " \\1<prd>", processed_text)
    processed_text = re.sub(" " + alphabets + "[.]", " \\1<prd>", processed_text)
    
    if "”" in processed_text:
        processed_text = processed_text.replace(".”", "”.")
    if "\"" in processed_text:
        processed_text = processed_text.replace(".\"", "\".")
    if "!" in processed_text:
        processed_text = processed_text.replace("!\"", "\"!")
    if "?" in processed_text:
        processed_text = processed_text.replace("?\"", "\"?")
    
    processed_text = processed_text.replace(".", ".<stop>")
    processed_text = processed_text.replace("?", "?<stop>")
    processed_text = processed_text.replace("!", "!<stop>")
    processed_text = processed_text.replace("<prd>", ".")
    
    sentences = processed_text.split("<stop>")
    sentences = [s.strip() for s in sentences if s.strip()]
    return pd.DataFrame(sentences, columns=['sentence'])

@st.cache_data
def sentiment_analysis(sentences):
    analyzer = SentimentIntensityAnalyzer()
    sentences['compound'] = [analyzer.polarity_scores(x)['compound'] for x in sentences['sentence']]
    sentences['neg'] = [analyzer.polarity_scores(x)['neg'] for x in sentences['sentence']]
    sentences['neu'] = [analyzer.polarity_scores(x)['neu'] for x in sentences['sentence']]
    sentences['pos'] = [analyzer.polarity_scores(x)['pos'] for x in sentences['sentence']]
    return sentences

@st.cache_data
def topic_modeling(sentences, num_topics=6):
    data = sentences['sentence'].values.tolist()
    
    def text_processing(texts):
        texts = [re.sub("[^a-zA-Z]+", " ", str(text)) for text in texts]
        texts = [[word for word in text.lower().split()] for text in texts]
        lmtzr = WordNetLemmatizer()
        texts = [[lmtzr.lemmatize(word) for word in text] for text in texts]
        stoplist = stopwords.words('english')
        texts = [[word for word in text if word not in stoplist] for text in texts]
        texts = [[word for word in tokens if len(word) >= 3] for tokens in texts]
        return texts
    
    processed_data = text_processing(data)
    dictionary = Dictionary(processed_data)
    corpus = [dictionary.doc2bow(text) for text in processed_data]
    
    # Find optimal number of topics
    if len(corpus) > 0:
        model = ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=num_topics, passes=20, random_state=1)
        topics = model.show_topics(formatted=False)
        topics_list = [[word for word, prob in topic] for topic_id, topic in topics]
        return topics_list
    return []

def generate_wordcloud(text, mask_path=None):
    stopwords_wc = set(stopwords.words("english"))
    wordcloud = WordCloud(
        max_words=321,
        stopwords=stopwords_wc,
        random_state=1,
        background_color='white',
        width=800,
        height=400
    ).generate(text)
    return wordcloud

def get_image_download_link(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

# Set page config
st.set_page_config(
    page_title="📚 Book Text Analyzer",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 2rem 0;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        padding: 1rem 0;
    }
    .stat-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">📚 Book Text Analyzer</div>', unsafe_allow_html=True)

# Sidebar for controls
st.sidebar.title("📁 Upload & Controls")
uploaded_file = st.sidebar.file_uploader("Upload a text file (.txt)", type=['txt'])

# Default text option
use_default = st.sidebar.checkbox("Use Great Expectations (default text)", value=False)

# Analysis options
st.sidebar.subheader("Analysis Options")
analyze_wordcloud = st.sidebar.checkbox("Word Cloud", value=True)
analyze_frequency = st.sidebar.checkbox("Word Frequency", value=True)
analyze_sentiment = st.sidebar.checkbox("Sentiment Analysis", value=True)
analyze_topic = st.sidebar.checkbox("Topic Modeling", value=True)

# Topic modeling parameters
if analyze_topic:
    num_topics = st.sidebar.slider("Number of Topics", 2, 12, 6)

# Main content
if uploaded_file or use_default:
    # Load text
    with st.spinner("Loading text..."):
        if use_default:
            # Create a default text file from Great Expectations
            try:
                with open('great_expectations.txt', 'r', encoding='utf8') as f:
                    text = f.read()
            except FileNotFoundError:
                # Sample text if file doesn't exist
                text = "This is a sample text for demonstration. The Great Expectations novel by Charles Dickens tells the story of Pip, an orphan. It explores themes of social class, ambition, and personal growth."
        else:
            text = load_text(uploaded_file)
        
        # Display basic stats
        total_chars = len(text)
        total_words = len(text.split())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📝 Total Characters", f"{total_chars:,}")
        with col2:
            st.metric("📖 Total Words", f"{total_words:,}")
        with col3:
            # Show first 100 chars
            st.metric("Preview", text[:100] + "...")

    # Preprocess
    clean_text = preprocess_text(text)
    tokens = tokenize_text(clean_text)
    
    # 1. Word Cloud
    if analyze_wordcloud:
        st.markdown('<div class="section-header">☁️ Word Cloud</div>', unsafe_allow_html=True)
        with st.spinner("Generating word cloud..."):
            wordcloud = generate_wordcloud(clean_text)
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
            plt.close()

    # 2. Word Frequency
    if analyze_frequency:
        st.markdown('<div class="section-header">📊 Word Frequency Analysis</div>', unsafe_allow_html=True)
        with st.spinner("Analyzing word frequency..."):
            fdist = nltk.FreqDist(tokens)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top 30 Words")
                top_words = pd.DataFrame(fdist.most_common(30), columns=['Word', 'Frequency'])
                st.dataframe(top_words, use_container_width=True, height=400)
            
            with col2:
                st.subheader("Frequency Distribution")
                fig, ax = plt.subplots(figsize=(10, 6))
                fdist.plot(30, ax=ax)
                st.pyplot(fig)
                plt.close()

    # 3. Sentiment Analysis
    if analyze_sentiment:
        st.markdown('<div class="section-header">😊 Sentiment Analysis</div>', unsafe_allow_html=True)
        with st.spinner("Performing sentiment analysis..."):
            # Split sentences
            sentences = split_sentences(text)
            # Remove first few rows if needed (like in notebook)
            if len(sentences) > 59:
                sentences = sentences.iloc[59:].reset_index(drop=True)
            
            # Perform sentiment
            sentences = sentiment_analysis(sentences)
            
            # Stats
            positive = len(sentences[sentences['compound'] > 0])
            negative = len(sentences[sentences['compound'] < 0])
            neutral = len(sentences[sentences['compound'] == 0])
            total = len(sentences)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sentences", total)
            with col2:
                st.metric("Positive", positive, f"{positive/total*100:.1f}%")
            with col3:
                st.metric("Neutral", neutral, f"{neutral/total*100:.1f}%")
            with col4:
                st.metric("Negative", negative, f"{negative/total*100:.1f}%")
            
            # Sentiment distribution
            st.subheader("Sentiment Distribution")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.hist(sentences['compound'], bins=50, color='steelblue', edgecolor='white')
            ax.set_xlabel('Compound Score')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Sentiment Scores')
            st.pyplot(fig)
            plt.close()
            
            # Sample sentences
            st.subheader("Sample Sentences by Sentiment")
            tab1, tab2, tab3 = st.tabs(["🔵 Positive", "⚪ Neutral", "🔴 Negative"])
            
            with tab1:
                positive_samples = sentences[sentences['compound'] > 0].head(10)
                for _, row in positive_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... (Score: {row['compound']:.2f})")
            
            with tab2:
                neutral_samples = sentences[sentences['compound'] == 0].head(10)
                for _, row in neutral_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... (Score: {row['compound']:.2f})")
            
            with tab3:
                negative_samples = sentences[sentences['compound'] < 0].head(10)
                for _, row in negative_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... (Score: {row['compound']:.2f})")

    # 4. Topic Modeling
    if analyze_topic:
        st.markdown('<div class="section-header">🎯 Topic Modeling</div>', unsafe_allow_html=True)
        with st.spinner(f"Identifying {num_topics} topics..."):
            if 'sentences' not in locals():
                sentences = split_sentences(text)
                if len(sentences) > 59:
                    sentences = sentences.iloc[59:].reset_index(drop=True)
            
            topics = topic_modeling(sentences, num_topics)
            
            if topics:
                for i, topic_words in enumerate(topics):
                    st.write(f"**Topic {i+1}:** {', '.join(topic_words[:10])}")
            else:
                st.warning("Not enough data for topic modeling. Try a longer text.")

else:
    st.info("👈 Please upload a text file or check 'Use Great Expectations' to begin analysis.")
    
    # Show example of what the app can do
    st.subheader("📖 Features")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - **Word Cloud** - Visual representation of word frequency
        - **Word Frequency** - Most common words and their frequencies
        - **Sentiment Analysis** - Positive, neutral, and negative sentiment classification
        - **Topic Modeling** - Identify key themes in your text
        """)
    with col2:
        st.markdown("""
        ### How to use:
        1. Upload a `.txt` file
        2. Or check "Use Great Expectations" for a sample
        3. Select analysis options in the sidebar
        4. Explore the results!
        """)

st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ using Streamlit")
```

## Installation & Running Instructions

Create a requirements.txt file:
```txt

streamlit==1.28.0
nltk==3.8.1
gensim==4.3.1
wordcloud==1.9.2
pandas==2.0.3
matplotlib==3.7.2
Pillow==10.0.0
```

Run the app:
```bash

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon'); nltk.download('wordnet')"

# Run the app
streamlit run app.py
```

Alternative Option: Flask Web App

If you prefer Flask instead of Streamlit:
```python

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
```

```text
Comparison of Options
Feature                 Streamlit       Flask       HTML Only
Ease of Development     ⭐⭐⭐⭐⭐      ⭐⭐⭐      ⭐⭐
Performance             ⭐⭐⭐          ⭐⭐⭐⭐    ⭐⭐⭐⭐⭐
Interactivity           ⭐⭐⭐⭐⭐      ⭐⭐⭐      ⭐
Data Visualization      ⭐⭐⭐⭐⭐      ⭐⭐        ⭐
Deployment              ⭐⭐⭐⭐        ⭐⭐⭐⭐    ⭐⭐⭐⭐⭐
Best For	Data apps, quick prototyping	Full web apps with custom frontend	Static content only
```

Recommendation

Use Streamlit for your book analyzer. It's:

    Fast to develop - your Jupyter code works almost 1:1

    Interactive - sliders, checkboxes, and real-time updates

    Great visualizations - Matplotlib, WordCloud, and more work perfectly

    Easy deployment - works on Streamlit Cloud, Hugging Face Spaces, Heroku

Would you like me to help you with any specific part of the implementation or add more features like:

    Book comparisons

    Chapter-by-chapter analysis

    Character tracking

    Plot progression over time

lets, see, would like to have:
1. option to read also other formats, not only txt,
2.  custom stopwords list (if you dont use English) 
what else can be interesting to have?
lets first fix and then start working

Great ideas! Let me think about what other features would make this a comprehensive book/text analyzer:
📚 Feature Wishlist for Book/Text Analyzer
File Format Support

    Text Formats: .txt, .pdf, .docx, .epub, .mobi

    Web Content: URL input (scrape text from articles/books)

    Copy/Paste: Direct text input for quick analysis

Language & Stopwords

    Multi-language stopwords - French, Spanish, German, Chinese, etc.

    Custom stopwords - Upload your own list or add words on-the-fly

    Language detection - Auto-detect text language

    Translation option - Analyze non-English texts with translation

Analysis Features

    Readability Scores - Flesch-Kincaid, Gunning Fog, SMOG

    Vocabulary Richness - Type-Token Ratio, unique words count

    Character Analysis - Track character mentions, relationships

    Chapter/Section Analysis - Split by chapters, analyze progression

    Named Entity Recognition - Identify people, places, organizations

    POS Tagging - Part-of-speech analysis

    N-gram Analysis - Common phrases (bigrams, trigrams)

    Emotion Detection - Beyond sentiment (joy, anger, sadness, etc.)

    Text Summarization - Auto-generate summary

    Keyword Extraction - Important keywords and phrases

Visualization Features

    Interactive Charts - Timeline of sentiment throughout the book

    Network Graphs - Character relationships

    Heat Maps - Word usage across chapters

    Comparisons - Compare two books side-by-side

    Progression Charts - How topics evolve over time

Export & Share

    PDF Report - Download analysis as PDF

    CSV Export - Export all data

    Share Results - Generate shareable link

    API Endpoints - For programmatic access

🎯 Priority Features for First Implementation

Let's focus on the most impactful features first:
Phase 1: Core Features

    ✅ Text upload (txt, pdf, docx, epub)

    ✅ Custom stopwords (upload or add)

    ✅ Multi-language support

    ✅ Word Cloud

    ✅ Word Frequency

    ✅ Sentiment Analysis

    ✅ Topic Modeling

Phase 2: Advanced Features

    Readability scores

    Chapter detection & analysis

    Named Entity Recognition

    Emotion detection

    Text summarization

    Book comparison (if multiple uploaded)

🚀 Updated Streamlit App with New Features

Let me write the complete implementation:


```python

# book_analyzer_app.py
import streamlit as st
import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem import WordNetLemmatizer
from gensim.corpora import Dictionary
from gensim.models import ldamodel
from wordcloud import WordCloud
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import ssl
import tempfile
import os
from pathlib import Path

# Additional imports for file formats
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# Language support - Additional stopwords
LANGUAGES = {
    'english': 'en',
    'spanish': 'es',
    'french': 'fr',
    'german': 'de',
    'italian': 'it',
    'portuguese': 'pt',
    'dutch': 'nl',
    'russian': 'ru',
    'chinese': 'zh',
    'arabic': 'ar',
    'japanese': 'ja',
    'korean': 'ko'
}

# Download NLTK data
@st.cache_resource
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
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)

download_nltk_data()

# Custom stopwords handler
@st.cache_data
def get_stopwords(language='english', custom_stopwords=None):
    try:
        if language in stopwords.fileids():
            stop_words = set(stopwords.words(language))
        else:
            stop_words = set(stopwords.words('english'))
    except:
        stop_words = set(stopwords.words('english'))
    
    if custom_stopwords:
        custom_list = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
        stop_words.update(custom_list)
    
    return stop_words

# File reader functions
def read_txt(file):
    return file.read().decode('utf-8')

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def read_epub(file):
    book = epub.read_epub(file)
    text = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content()
            soup = BeautifulSoup(content, 'html.parser')
            text += soup.get_text() + "\n"
    return text

def read_text_file(uploaded_file):
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type == 'txt':
        return read_txt(uploaded_file)
    elif file_type == 'pdf':
        return read_pdf(uploaded_file)
    elif file_type == 'docx':
        return read_docx(uploaded_file)
    elif file_type == 'epub':
        return read_epub(uploaded_file)
    else:
        st.error(f"Unsupported file format: {file_type}")
        return None

@st.cache_data
def extract_metadata(text):
    lines = text.split('\n')
    # Try to find title and author
    title = "Unknown"
    author = "Unknown"
    
    # Simple detection - can be improved
    for line in lines[:50]:
        if 'title' in line.lower() or 'book' in line.lower():
            if len(line) < 100 and len(line) > 5:
                title = line.strip()
                break
    
    for line in lines[:50]:
        if 'author' in line.lower() or 'by' in line.lower():
            if len(line) < 100 and len(line) > 5:
                author = line.strip().replace('Author:', '').replace('by', '').strip()
                break
    
    return title, author

@st.cache_data
def preprocess_text(text):
    word_cloud_text = text.lower()
    word_cloud_text = re.sub("[^a-zA-Z0-9]", " ", word_cloud_text)
    return word_cloud_text

@st.cache_data
def tokenize_text(text, stop_words):
    tokens = word_tokenize(text)
    tokens = [word.lower() for word in tokens if word.isalpha()]
    tokens = [word for word in tokens if word not in stop_words]
    tokens = [word for word in tokens if len(word) >= 3]
    return tokens

@st.cache_data
def split_sentences(text):
    # Same as before but with improved split
    alphabets = "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Rev|Hon|Sen|Rep)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co|Corp|LLC|Assoc|Bro|Sis)"
    starters = "(Mr|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|He\\s|She\\s|It\\s|They\\s|Their\\s|Our\\s|We\\s|But\\s|However\\s|That\\s|This\\s|Wherever|Who|Whom|Which|When|Why|How)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov|edu|me|co\\.uk|uk)"
    digits = "([0-9])"
    
    processed_text = " " + text + "  "
    processed_text = processed_text.replace("\n", " ")
    processed_text = re.sub(prefixes, "\\1<prd>", processed_text)
    processed_text = re.sub(websites, "<prd>\\1", processed_text)
    processed_text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", processed_text)
    
    if "..." in processed_text:
        processed_text = processed_text.replace("...", "<prd><prd><prd>")
    if "Ph.D" in processed_text:
        processed_text = processed_text.replace("Ph.D.", "Ph<prd>D<prd>")
    
    processed_text = re.sub("\\s" + alphabets + "[.] ", " \\1<prd> ", processed_text)
    processed_text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", processed_text)
    processed_text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", processed_text)
    processed_text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", processed_text)
    processed_text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", processed_text)
    processed_text = re.sub(" " + suffixes + "[.]", " \\1<prd>", processed_text)
    processed_text = re.sub(" " + alphabets + "[.]", " \\1<prd>", processed_text)
    
    if "”" in processed_text:
        processed_text = processed_text.replace(".”", "”.")
    if "\"" in processed_text:
        processed_text = processed_text.replace(".\"", "\".")
    if "!" in processed_text:
        processed_text = processed_text.replace("!\"", "\"!")
    if "?" in processed_text:
        processed_text = processed_text.replace("?\"", "\"?")
    
    processed_text = processed_text.replace(".", ".<stop>")
    processed_text = processed_text.replace("?", "?<stop>")
    processed_text = processed_text.replace("!", "!<stop>")
    processed_text = processed_text.replace("<prd>", ".")
    
    sentences = processed_text.split("<stop>")
    sentences = [s.strip() for s in sentences if s.strip()]
    return pd.DataFrame(sentences, columns=['sentence'])

@st.cache_data
def sentiment_analysis(sentences):
    analyzer = SentimentIntensityAnalyzer()
    sentences['compound'] = [analyzer.polarity_scores(x)['compound'] for x in sentences['sentence']]
    sentences['neg'] = [analyzer.polarity_scores(x)['neg'] for x in sentences['sentence']]
    sentences['neu'] = [analyzer.polarity_scores(x)['neu'] for x in sentences['sentence']]
    sentences['pos'] = [analyzer.polarity_scores(x)['pos'] for x in sentences['sentence']]
    return sentences

@st.cache_data
def calculate_readability(text):
    sentences = re.split(r'[.!?]+', text)
    words = text.split()
    
    # Remove empty sentences
    sentences = [s for s in sentences if s.strip()]
    
    if not sentences or not words:
        return None
    
    # Flesch Reading Ease
    total_syllables = sum(count_syllables(word) for word in words)
    flesch_score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (total_syllables / len(words))
    
    # Flesch-Kincaid Grade Level
    fk_score = 0.39 * (len(words) / len(sentences)) + 11.8 * (total_syllables / len(words)) - 15.59
    
    # Gunning Fog Index
    complex_words = sum(1 for word in words if count_syllables(word) >= 3)
    fog_score = 0.4 * ((len(words) / len(sentences)) + 100 * (complex_words / len(words)))
    
    # Average words per sentence
    avg_words = len(words) / len(sentences)
    
    return {
        'flesch_reading_ease': flesch_score,
        'flesch_kincaid_grade': fk_score,
        'gunning_fog': fog_score,
        'avg_words_per_sentence': avg_words,
        'total_sentences': len(sentences),
        'total_words': len(words),
        'total_syllables': total_syllables
    }

def count_syllables(word):
    # Simple syllable counter
    word = word.lower()
    vowels = "aeiouy"
    count = 0
    prev_char = ''
    for char in word:
        if char in vowels and prev_char not in vowels:
            count += 1
        prev_char = char
    if word.endswith('e'):
        count -= 1
    if count == 0:
        count = 1
    return count

@st.cache_data
def topic_modeling(sentences, num_topics=6):
    data = sentences['sentence'].values.tolist()
    
    def text_processing(texts):
        texts = [re.sub("[^a-zA-Z]+", " ", str(text)) for text in texts]
        texts = [[word for word in text.lower().split()] for text in texts]
        lmtzr = WordNetLemmatizer()
        texts = [[lmtzr.lemmatize(word) for word in text] for text in texts]
        stoplist = stopwords.words('english')
        texts = [[word for word in text if word not in stoplist] for text in texts]
        texts = [[word for word in tokens if len(word) >= 3] for tokens in texts]
        return texts
    
    processed_data = text_processing(data)
    dictionary = Dictionary(processed_data)
    corpus = [dictionary.doc2bow(text) for text in processed_data]
    
    if len(corpus) > 0 and len(dictionary) > 0:
        model = ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=num_topics, passes=20, random_state=1)
        topics = model.show_topics(formatted=False)
        topics_list = [[word for word, prob in topic] for topic_id, topic in topics]
        return topics_list
    return []

def generate_wordcloud(text, stop_words, max_words=200):
    wordcloud = WordCloud(
        max_words=max_words,
        stopwords=stop_words,
        random_state=1,
        background_color='white',
        width=800,
        height=400,
        colormap='viridis'
    ).generate(text)
    return wordcloud

# Page configuration
st.set_page_config(
    page_title="📚 Book Text Analyzer Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 2rem 0;
    }
    .section-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #2c3e50;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.5rem;
    }
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">📚 Book Text Analyzer Pro</div>', unsafe_allow_html=True)
st.markdown("### Advanced Text Analysis for Books, Articles, and Documents")

# Sidebar
st.sidebar.title("⚙️ Controls")

with st.sidebar.expander("📂 File Upload", expanded=True):
    uploaded_file = st.sidebar.file_uploader(
        "Upload your book/document",
        type=['txt', 'pdf', 'docx', 'epub'],
        help="Supported formats: TXT, PDF, DOCX, EPUB"
    )
    
    # Or paste text directly
    direct_text = st.sidebar.text_area(
        "Or paste text directly",
        height=150,
        placeholder="Paste your text here..."
    )

with st.sidebar.expander("🌍 Language Settings", expanded=False):
    language = st.selectbox(
        "Select language",
        list(LANGUAGES.keys()),
        help="Choose the language of your text"
    )
    
    st.markdown("**Custom Stopwords**")
    custom_stop = st.text_input(
        "Add custom stopwords (comma-separated)",
        placeholder="e.g., chapter, preface, introduction"
    )

with st.sidebar.expander("🔬 Analysis Options", expanded=True):
    analyze_wordcloud = st.checkbox("☁️ Word Cloud", value=True)
    analyze_frequency = st.checkbox("📊 Word Frequency", value=True)
    analyze_sentiment = st.checkbox("😊 Sentiment Analysis", value=True)
    analyze_readability = st.checkbox("📖 Readability Scores", value=True)
    analyze_topic = st.checkbox("🎯 Topic Modeling", value=True)
    
    if analyze_topic:
        num_topics = st.slider("Number of Topics", 2, 12, 6)
    
    max_words = st.slider("Max words in word cloud", 50, 500, 200)

with st.sidebar.expander("💾 Export Options", expanded=False):
    if st.button("📥 Download Report"):
        st.info("Report generation coming soon!")

# Main content
if uploaded_file or direct_text:
    # Load text
    with st.spinner("📖 Loading your text..."):
        if uploaded_file:
            text = read_text_file(uploaded_file)
            if text is None:
                st.error("Failed to read the file. Please try another format.")
                st.stop()
            filename = uploaded_file.name
        else:
            text = direct_text
            filename = "paste_text.txt"
        
        if not text or len(text.strip()) < 10:
            st.warning("⚠️ The text is too short for meaningful analysis. Please provide more text.")
            st.stop()
        
        # Extract metadata
        title, author = extract_metadata(text)
        
        # Get stopwords
        stop_words = get_stopwords(language, custom_stop)
        
        # Basic stats
        total_chars = len(text)
        total_words = len(text.split())
        total_lines = len(text.split('\n'))
        
        # Display stats
        st.markdown("### 📊 Document Statistics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="metric-value">{total_chars:,}</div>
                <div class="metric-label">Characters</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="metric-value">{total_words:,}</div>
                <div class="metric-label">Words</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="metric-value">{total_lines:,}</div>
                <div class="metric-label">Lines</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="metric-value" style="font-size:1.2rem">{title[:30] + '...' if len(title) > 30 else title}</div>
                <div class="metric-label">Title</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown(f"""
            <div class="stat-card">
                <div class="metric-value" style="font-size:1.2rem">{author[:30] + '...' if len(author) > 30 else author}</div>
                <div class="metric-label">Author</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**File**: {filename} | **Language**: {language}")
        
        # Show preview
        with st.expander("📄 Text Preview (first 500 characters)"):
            st.text(text[:500] + "..." if len(text) > 500 else text)
    
    # Preprocess
    clean_text = preprocess_text(text)
    tokens = tokenize_text(clean_text, stop_words)
    
    if not tokens:
        st.warning("⚠️ No tokens found after preprocessing. Try adjusting stopwords.")
        st.stop()
    
    # Split sentences for sentiment
    sentences = split_sentences(text)
    if len(sentences) > 59:
        sentences = sentences.iloc[59:].reset_index(drop=True)
    
    # 1. Word Cloud
    if analyze_wordcloud:
        st.markdown('<div class="section-header">☁️ Word Cloud</div>', unsafe_allow_html=True)
        with st.spinner("🎨 Generating word cloud..."):
            try:
                wordcloud = generate_wordcloud(clean_text, stop_words, max_words)
                fig, ax = plt.subplots(figsize=(14, 8))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.error(f"Error generating word cloud: {e}")

    # 2. Word Frequency
    if analyze_frequency:
        st.markdown('<div class="section-header">📊 Word Frequency Analysis</div>', unsafe_allow_html=True)
        with st.spinner("📊 Analyzing word frequency..."):
            fdist = nltk.FreqDist(tokens)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top 30 Words")
                top_words = pd.DataFrame(fdist.most_common(30), columns=['Word', 'Frequency'])
                top_words['Percentage'] = (top_words['Frequency'] / len(tokens) * 100).round(2)
                st.dataframe(top_words, use_container_width=True, height=400)
                
                # Download option
                csv = top_words.to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="word_frequency.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.subheader("📈 Frequency Distribution")
                fig, ax = plt.subplots(figsize=(10, 6))
                fdist.plot(30, ax=ax)
                st.pyplot(fig)
                plt.close()
                
                # Additional stats
                st.subheader("📋 Vocabulary Statistics")
                col1b, col2b = st.columns(2)
                with col1b:
                    st.metric("Unique Words", len(fdist))
                    st.metric("Type-Token Ratio", f"{len(fdist)/len(tokens):.3f}")
                with col2b:
                    st.metric("Most Common", fdist.most_common(1)[0][0] if fdist else "N/A")
                    st.metric("Frequency (most common)", fdist.most_common(1)[0][1] if fdist else "N/A")

    # 3. Sentiment Analysis
    if analyze_sentiment:
        st.markdown('<div class="section-header">😊 Sentiment Analysis</div>', unsafe_allow_html=True)
        with st.spinner("🔍 Analyzing sentiment..."):
            sentences = sentiment_analysis(sentences)
            
            # Stats
            positive = len(sentences[sentences['compound'] > 0])
            negative = len(sentences[sentences['compound'] < 0])
            neutral = len(sentences[sentences['compound'] == 0])
            total = len(sentences)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📝 Total Sentences", total)
            with col2:
                st.metric("😊 Positive", positive, f"{positive/total*100:.1f}%")
            with col3:
                st.metric("😐 Neutral", neutral, f"{neutral/total*100:.1f}%")
            with col4:
                st.metric("😞 Negative", negative, f"{negative/total*100:.1f}%")
            
            # Pie chart
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sentiment Distribution")
                fig, ax = plt.subplots(figsize=(8, 6))
                labels = ['Positive', 'Negative', 'Neutral']
                sizes = [positive, negative, neutral]
                colors = ['#2ecc71', '#e74c3c', '#95a5a6']
                ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')
                st.pyplot(fig)
                plt.close()
            
            with col2:
                st.subheader("Sentiment Score Distribution")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(sentences['compound'], bins=50, color='steelblue', edgecolor='white', alpha=0.7)
                ax.axvline(x=0, color='red', linestyle='--', linewidth=2)
                ax.set_xlabel('Compound Score')
                ax.set_ylabel('Frequency')
                ax.set_title('Distribution of Sentiment Scores')
                st.pyplot(fig)
                plt.close()
            
            # Sample sentences
            st.subheader("📝 Sample Sentences by Sentiment")
            tab1, tab2, tab3 = st.tabs(["😊 Positive", "😐 Neutral", "😞 Negative"])
            
            with tab1:
                positive_samples = sentences[sentences['compound'] > 0].head(5)
                for _, row in positive_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... *(Score: {row['compound']:.2f})*")
            
            with tab2:
                neutral_samples = sentences[sentences['compound'] == 0].head(5)
                for _, row in neutral_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... *(Score: {row['compound']:.2f})*")
            
            with tab3:
                negative_samples = sentences[sentences['compound'] < 0].head(5)
                for _, row in negative_samples.iterrows():
                    st.write(f"• {row['sentence'][:200]}... *(Score: {row['compound']:.2f})*")

    # 4. Readability Scores
    if analyze_readability:
        st.markdown('<div class="section-header">📖 Readability Analysis</div>', unsafe_allow_html=True)
        with st.spinner("📊 Calculating readability scores..."):
            readability = calculate_readability(text)
            
            if readability:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Flesch Reading Ease",
                        f"{readability['flesch_reading_ease']:.1f}",
                        help="90-100: Very Easy, 60-70: Plain English, 30-50: Difficult, 0-30: Very Difficult"
                    )
                
                with col2:
                    st.metric(
                        "Flesch-Kincaid Grade",
                        f"{readability['flesch_kincaid_grade']:.1f}",
                        help="US grade level required to understand the text"
                    )
                
                with col3:
                    st.metric(
                        "Gunning Fog Index",
                        f"{readability['gunning_fog']:.1f}",
                        help="Years of formal education needed to understand"
                    )
                
                with col4:
                    st.metric(
                        "Avg Words/Sentence",
                        f"{readability['avg_words_per_sentence']:.1f}",
                        help="Average number of words per sentence"
                    )
                
                # Interpretation
                st.subheader("📖 Readability Interpretation")
                
                flesch = readability['flesch_reading_ease']
                if flesch >= 90:
                    level = "Very Easy (5th grade)"
                    icon = "📘"
                elif flesch >= 80:
                    level = "Easy (6th grade)"
                    icon = "📗"
                elif flesch >= 70:
                    level = "Plain English (7th grade)"
                    icon = "📙"
                elif flesch >= 60:
                    level = "Fairly Easy (8th-9th grade)"
                    icon = "📒"
                elif flesch >= 50:
                    level = "Fairly Difficult (10th-12th grade)"
                    icon = "📕"
                else:
                    level = "Difficult (College level)"
                    icon = "📖"
                
                st.info(f"{icon} **Reading Level**: {level}")
                
                st.markdown("""
                **Understanding Readability Scores:**
                - **Flesch Reading Ease**: Higher scores = easier to read
                - **Flesch-Kincaid Grade**: Lower scores = easier to read
                - **Gunning Fog Index**: Lower scores = easier to read
                - **Recommended**: Aim for Flesch 60-70 for general audiences
                """)

    # 5. Topic Modeling
    if analyze_topic:
        st.markdown('<div class="section-header">🎯 Topic Modeling</div>', unsafe_allow_html=True)
        with st.spinner(f"🔍 Identifying {num_topics} topics..."):
            topics = topic_modeling(sentences, num_topics)
            
            if topics:
                # Display topics in columns
                cols = st.columns(min(num_topics, 4))
                for i, topic_words in enumerate(topics):
                    col_idx = i % len(cols)
                    with cols[col_idx]:
                        st.markdown(f"""
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; border-left: 4px solid #1f77b4;">
                            <strong>Topic {i+1}</strong>
                            <p style="font-size: 0.9rem; margin-top: 0.5rem;">{', '.join(topic_words[:15])}</p>
                            <small style="color: #6c757d;">Keywords: {', '.join(topic_words[:5])}</small>
                        </div>
                        """, unsafe_allow_html=True)
                
                # All topics in a table
                with st.expander("📋 View all topics"):
                    topic_df = pd.DataFrame({
                        'Topic': [f"Topic {i+1}" for i in range(len(topics))],
                        'Keywords': [', '.join(t[:10]) for t in topics]
                    })
                    st.dataframe(topic_df, use_container_width=True)
            else:
                st.warning("⚠️ Not enough data for topic modeling. Try a longer text or reduce the number of topics.")

else:
    # Welcome message with features
    st.markdown("""
    ## 👈 Welcome to Book Text Analyzer Pro!
    
    ### 🚀 Features
    - **Multi-format Support**: Upload TXT, PDF, DOCX, or EPUB files
    - **Multi-language**: Supports 12+ languages with custom stopwords
    - **Sentiment Analysis**: Understand the emotional tone of your text
    - **Readability Scores**: Measure how easy or difficult your text is to read
    - **Word Cloud**: Visualize the most frequent words
    - **Topic Modeling**: Discover hidden themes in your text
    - **Word Frequency**: See which words are used most often
    
    ### 📖 Quick Start
    1. Upload a book or paste text using the sidebar
    2. Select your language
    3. Customize analysis options
    4. Explore the results!
    
    ### 💡 Pro Tips
    - For better results, use texts with at least 500 words
    - Add custom stopwords to remove irrelevant words
    - Try different numbers of topics for topic modeling
    - Compare multiple texts by uploading them one at a time
    """)
    
    # Sample text option
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📚 Load Sample Text (Great Expectations)"):
            try:
                with open('great_expectations.txt', 'r', encoding='utf8') as f:
                    sample_text = f.read()
                st.session_state['sample_text'] = sample_text
                st.rerun()
            except:
                st.error("Sample text file not found. Please upload your own text.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 2rem 0;">
    Built with ❤️ using Streamlit | 📚 Book Text Analyzer Pro
</div>
""", unsafe_allow_html=True)
```


📦 Updated Requirements

```txt

# requirements.txt
streamlit==1.28.0
nltk==3.8.1
gensim==4.3.1
wordcloud==1.9.2
pandas==2.0.3
matplotlib==3.7.2
Pillow==10.0.0

# New dependencies for file formats
PyPDF2==3.0.1
python-docx==1.0.0
EbookLib==0.18
beautifulsoup4==4.12.2
lxml==4.9.3
```

🎯 Next Steps

Let me know if you want me to:

    Add more languages - Which languages do you need?

    Implement specific features - Any priority from the wishlist?

    Add comparison mode - Compare two books side-by-side

    Add chapter detection - Auto-detect and analyze chapters

    Add export to PDF - Generate professional reports

    Add API - For programmatic access

    Add visualization - Timeline

