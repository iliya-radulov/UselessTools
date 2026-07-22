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