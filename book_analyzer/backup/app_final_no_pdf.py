# app_final_no_pdf.py
# Version without PDF export (uses simple text export instead)

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
import ssl
from io import BytesIO, StringIO
import base64
from datetime import datetime
import json

# File format imports
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# Language configuration
LANGUAGES = {
    'English': {'code': 'en', 'nltk_stopwords': 'english', 'flag': '🇬🇧'},
    'Bulgarian': {'code': 'bg', 'nltk_stopwords': 'bulgarian', 'flag': '🇧🇬'},
    'Spanish': {'code': 'es', 'nltk_stopwords': 'spanish', 'flag': '🇪🇸'},
    'French': {'code': 'fr', 'nltk_stopwords': 'french', 'flag': '🇫🇷'},
    'German': {'code': 'de', 'nltk_stopwords': 'german', 'flag': '🇩🇪'},
    'Italian': {'code': 'it', 'nltk_stopwords': 'italian', 'flag': '🇮🇹'},
    'Portuguese': {'code': 'pt', 'nltk_stopwords': 'portuguese', 'flag': '🇵🇹'},
    'Dutch': {'code': 'nl', 'nltk_stopwords': 'dutch', 'flag': '🇳🇱'},
    'Russian': {'code': 'ru', 'nltk_stopwords': 'russian', 'flag': '🇷🇺'},
    'Arabic': {'code': 'ar', 'nltk_stopwords': 'arabic', 'flag': '🇸🇦'},
    'Turkish': {'code': 'tr', 'nltk_stopwords': 'turkish', 'flag': '🇹🇷'},
    'Greek': {'code': 'el', 'nltk_stopwords': 'greek', 'flag': '🇬🇷'},
    'Swedish': {'code': 'sv', 'nltk_stopwords': 'swedish', 'flag': '🇸🇪'},
    'Norwegian': {'code': 'no', 'nltk_stopwords': 'norwegian', 'flag': '🇳🇴'},
    'Danish': {'code': 'da', 'nltk_stopwords': 'danish', 'flag': '🇩🇰'},
    'Finnish': {'code': 'fi', 'nltk_stopwords': 'finnish', 'flag': '🇫🇮'},
    'Hungarian': {'code': 'hu', 'nltk_stopwords': 'hungarian', 'flag': '🇭🇺'},
    'Polish': {'code': 'pl', 'nltk_stopwords': 'polish', 'flag': '🇵🇱'},
    'Czech': {'code': 'cs', 'nltk_stopwords': 'czech', 'flag': '🇨🇿'},
    'Romanian': {'code': 'ro', 'nltk_stopwords': 'romanian', 'flag': '🇷🇴'},
    'Slovak': {'code': 'sk', 'nltk_stopwords': 'slovak', 'flag': '🇸🇰'},
    'Slovenian': {'code': 'sl', 'nltk_stopwords': 'slovenian', 'flag': '🇸🇮'},
    'Estonian': {'code': 'et', 'nltk_stopwords': 'estonian', 'flag': '🇪🇪'},
    'Latvian': {'code': 'lv', 'nltk_stopwords': 'latvian', 'flag': '🇱🇻'},
    'Lithuanian': {'code': 'lt', 'nltk_stopwords': 'lithuanian', 'flag': '🇱🇹'},
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
    
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        
        # Download additional language resources if available
        for lang in ['spanish', 'french', 'german', 'italian', 'portuguese', 
                     'dutch', 'russian', 'arabic', 'turkish']:
            try:
                nltk.download(f'stopwords_{lang}', quiet=True)
            except:
                pass
    except:
        pass

download_nltk_data()

# File readers
def read_txt(file):
    try:
        return file.read().decode('utf-8')
    except:
        try:
            return file.read().decode('latin-1')
        except:
            return file.read().decode('utf-8', errors='ignore')

def read_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def read_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return ""

def read_epub(file):
    try:
        book = epub.read_epub(file)
        text = ""
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                text += soup.get_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading EPUB: {e}")
        return ""

def read_file(uploaded_file):
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

# Text analysis functions
@st.cache_data
def analyze_text(text, language='English', custom_stopwords=None, num_topics=3):
    """Complete text analysis"""
    
    # Get stopwords
    try:
        lang_code = LANGUAGES[language]['nltk_stopwords']
        if lang_code in stopwords.fileids():
            stop_words = set(stopwords.words(lang_code))
        else:
            stop_words = set(stopwords.words('english'))
    except:
        stop_words = set(stopwords.words('english'))
    
    # Add custom stopwords
    if custom_stopwords:
        extra = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
        stop_words.update(extra)
    
    # Clean text
    clean_text = text.lower()
    clean_text = re.sub("[^a-zA-Z0-9\\s]", " ", clean_text)
    
    # Tokenize
    tokens = word_tokenize(clean_text)
    tokens = [word for word in tokens if word not in stop_words]
    tokens = [word for word in tokens if len(word) >= 3]
    
    # Word frequency
    fdist = nltk.FreqDist(tokens)
    
    # Get sentences for sentiment
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    
    # Sentiment analysis
    sentiment_results = []
    if sentences:
        analyzer = SentimentIntensityAnalyzer()
        for s in sentences[:200]:  # Limit for performance
            scores = analyzer.polarity_scores(s)
            sentiment_results.append({
                'sentence': s[:200],
                'compound': scores['compound'],
                'neg': scores['neg'],
                'neu': scores['neu'],
                'pos': scores['pos']
            })
    
    # Topic modeling
    topics = []
    if len(sentences) > 20:
        try:
            processed_data = []
            for s in sentences[:200]:
                words = word_tokenize(s.lower())
                words = [w for w in words if w.isalpha()]
                words = [w for w in words if w not in stop_words]
                words = [w for w in words if len(w) >= 3]
                if words:
                    processed_data.append(words)
            
            if len(processed_data) > 10:
                dictionary = Dictionary(processed_data)
                dictionary.filter_extremes(no_below=2, no_above=0.5)
                corpus = [dictionary.doc2bow(text) for text in processed_data]
                
                if len(corpus) > 0 and len(dictionary) > 0:
                    model = ldamodel.LdaModel(
                        corpus, 
                        id2word=dictionary, 
                        num_topics=num_topics, 
                        passes=10,
                        random_state=1
                    )
                    topic_data = model.show_topics(formatted=False)
                    for topic in topic_data:
                        if isinstance(topic, tuple) and len(topic) >= 2:
                            words = [word for word, prob in topic[1] if isinstance(word, str)]
                            topics.append(words)
        except:
            pass
    
    # Readability
    readability = {}
    if sentences and tokens:
        try:
            def count_syllables(word):
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
            
            total_sentences = len(sentences)
            total_words = len(tokens)
            total_syllables = sum(count_syllables(w) for w in tokens)
            
            if total_sentences > 0 and total_words > 0:
                flesch_score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
                fk_score = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
                avg_words = total_words / total_sentences
                
                readability = {
                    'flesch_score': flesch_score,
                    'fk_score': fk_score,
                    'avg_words': avg_words,
                    'total_sentences': total_sentences,
                    'total_words': total_words
                }
        except:
            pass
    
    return {
        'tokens': tokens,
        'fdist': fdist,
        'sentiment': sentiment_results,
        'topics': topics,
        'readability': readability,
        'clean_text': clean_text,
        'stop_words': stop_words,
        'total_words': len(tokens),
        'unique_words': len(fdist)
    }

# Simple text report (no PDF library needed)
def generate_text_report(results, filename):
    """Generate a text-based report"""
    report = []
    report.append("=" * 60)
    report.append(f"BOOK ANALYSIS REPORT")
    report.append("=" * 60)
    report.append(f"File: {filename}")
    report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Statistics
    report.append("STATISTICS")
    report.append("-" * 60)
    report.append(f"Total Words: {results['total_words']:,}")
    report.append(f"Unique Words: {results['unique_words']:,}")
    report.append(f"Sentences Analyzed: {len(results['sentiment'])}")
    report.append("")
    
    # Readability
    if results['readability']:
        r = results['readability']
        report.append("READABILITY")
        report.append("-" * 60)
        report.append(f"Flesch Reading Ease: {r['flesch_score']:.1f}")
        report.append(f"Flesch-Kincaid Grade: {r['fk_score']:.1f}")
        report.append(f"Avg Words/Sentence: {r['avg_words']:.1f}")
        report.append("")
    
    # Top words
    report.append("TOP 20 WORDS")
    report.append("-" * 60)
    for i, (word, freq) in enumerate(results['fdist'].most_common(20), 1):
        report.append(f"{i:2}. {word:15} {freq:5}")
    report.append("")
    
    # Sentiment
    if results['sentiment']:
        df = pd.DataFrame(results['sentiment'])
        positive = len(df[df['compound'] > 0.05])
        negative = len(df[df['compound'] < -0.05])
        neutral = len(df[(df['compound'] >= -0.05) & (df['compound'] <= 0.05)])
        
        report.append("SENTIMENT ANALYSIS")
        report.append("-" * 60)
        report.append(f"Positive: {positive} ({positive/len(df)*100:.1f}%)")
        report.append(f"Neutral:  {neutral} ({neutral/len(df)*100:.1f}%)")
        report.append(f"Negative: {negative} ({negative/len(df)*100:.1f}%)")
        report.append(f"Average Score: {df['compound'].mean():.3f}")
        report.append("")
    
    # Topics
    if results['topics']:
        report.append("TOPICS DISCOVERED")
        report.append("-" * 60)
        for i, topic in enumerate(results['topics'], 1):
            report.append(f"Topic {i}: {', '.join(topic[:10])}")
        report.append("")
    
    report.append("=" * 60)
    report.append("End of Report")
    
    return "\n".join(report)

# Streamlit UI
st.set_page_config(
    page_title="📚 Book Analyzer Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(120deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        padding: 0.5rem 0;
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .language-tag {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        background: #e9ecef;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📚 Book Analyzer Pro</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Controls")

# File upload
with st.sidebar.expander("📂 Upload File", expanded=True):
    uploaded_file = st.sidebar.file_uploader(
        "Choose a file",
        type=['txt', 'pdf', 'docx', 'epub'],
        help="Supported: TXT, PDF, DOCX, EPUB"
    )
    
    # Direct text input
    direct_text = st.sidebar.text_area(
        "Or paste text directly",
        height=100,
        placeholder="Paste your text here..."
    )

# Language selection
with st.sidebar.expander("🌍 Language Settings", expanded=True):
    language = st.selectbox(
        "Select language",
        list(LANGUAGES.keys()),
        index=0,
        help="Choose the language of your text"
    )
    
    # Show language info
    lang_info = LANGUAGES[language]
    st.caption(f"Code: {lang_info['code']} | Stopwords: {lang_info['nltk_stopwords']}")
    
    # Custom stopwords
    custom_stopwords = st.text_input(
        "Add custom stopwords (comma-separated)",
        placeholder="e.g., chapter, introduction, volume"
    )

# Analysis options
with st.sidebar.expander("🔬 Analysis Options", expanded=True):
    show_wordcloud = st.checkbox("☁️ Word Cloud", value=True)
    show_frequency = st.checkbox("📊 Word Frequency", value=True)
    show_sentiment = st.checkbox("😊 Sentiment Analysis", value=True)
    show_readability = st.checkbox("📖 Readability Scores", value=True)
    show_topic = st.checkbox("🎯 Topic Modeling", value=True)
    
    if show_topic:
        num_topics = st.slider("Number of Topics", 2, 8, 3)
    
    max_words = st.slider("Max words in word cloud", 50, 500, 200)
    sample_limit = st.slider("Sentences to analyze", 50, 500, 200)

# Export options
with st.sidebar.expander("📤 Export", expanded=False):
    st.markdown("Download analysis results:")
    export_format = st.selectbox("Format", ["Text Report", "CSV Data", "JSON"])
    
    if st.button("📥 Generate Report"):
        st.session_state['export_trigger'] = True

# Language stats
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Supported Languages:**  
🇬🇧 English 🇧🇬 Bulgarian 🇪🇸 Spanish 🇫🇷 French  
🇩🇪 German 🇮🇹 Italian 🇵🇹 Portuguese 🇳🇱 Dutch  
🇷🇺 Russian 🇸🇦 Arabic 🇹🇷 Turkish 🇬🇷 Greek  
🇸🇪 Swedish 🇳🇴 Norwegian 🇩🇰 Danish 🇫🇮 Finnish  
🇭🇺 Hungarian 🇵🇱 Polish 🇨🇿 Czech 🇷🇴 Romanian  
🇸🇰 Slovak 🇸🇮 Slovenian 🇪🇪 Estonian 🇱🇻 Latvian 🇱🇹 Lithuanian
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**Version:** 4.0 | Made with ❤️")

# Main content
if uploaded_file or direct_text:
    # Load text
    with st.spinner("📖 Loading your document..."):
        if uploaded_file:
            text = read_file(uploaded_file)
            if text is None:
                st.error("Failed to read the file.")
                st.stop()
            filename = uploaded_file.name
        else:
            text = direct_text
            filename = "pasted_text.txt"
        
        if not text or len(text.strip()) < 20:
            st.warning("⚠️ Text too short. Please provide more content.")
            st.stop()
    
    # Analyze
    with st.spinner("🔍 Analyzing text..."):
        results = analyze_text(text, language, custom_stopwords, num_topics)
    
    # Display results
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{results['total_words']:,}</h3>
            <small>Total Words</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{results['unique_words']:,}</h3>
            <small>Unique Words</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{len(results['sentiment']):,}</h3>
            <small>Sentences Analyzed</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if results['readability']:
            flesch = results['readability'].get('flesch_score', 0)
            if flesch > 70:
                label = "Easy 📘"
            elif flesch > 50:
                label = "Medium 📙"
            else:
                label = "Complex 📕"
            st.markdown(f"""
            <div class="stat-box">
                <h3>{label}</h3>
                <small>Readability: {flesch:.1f}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Preview
    with st.expander("📄 Text Preview (first 300 characters)"):
        st.text(text[:300] + "..." if len(text) > 300 else text)
    
    # 1. Word Cloud
    if show_wordcloud and results['clean_text']:
        st.markdown('<div class="section-header">☁️ Word Cloud</div>', unsafe_allow_html=True)
        with st.spinner("🎨 Generating word cloud..."):
            try:
                wordcloud = WordCloud(
                    max_words=max_words,
                    background_color='white',
                    random_state=1,
                    colormap='viridis'
                ).generate(results['clean_text'])
                
                fig, ax = plt.subplots(figsize=(14, 8))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.error(f"Error generating word cloud: {e}")
    
    # 2. Word Frequency
    if show_frequency and results['fdist']:
        st.markdown('<div class="section-header">📊 Word Frequency</div>', unsafe_allow_html=True)
        
        fdist = results['fdist']
        top_words = pd.DataFrame(fdist.most_common(30), columns=['Word', 'Frequency'])
        top_words['Percentage'] = (top_words['Frequency'] / results['total_words'] * 100).round(2)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(top_words, use_container_width=True, height=400)
        
        with col2:
            top_20 = fdist.most_common(20)
            words = [item[0] for item in top_20]
            freqs = [item[1] for item in top_20]
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(words, freqs, color='steelblue')
            ax.set_xlabel('Words')
            ax.set_ylabel('Frequency')
            ax.set_title('Top 20 Most Frequent Words')
            ax.tick_params(axis='x', rotation=45)
            st.pyplot(fig)
            plt.close()
    
    # 3. Sentiment
    if show_sentiment and results['sentiment']:
        st.markdown('<div class="section-header">😊 Sentiment Analysis</div>', unsafe_allow_html=True)
        
        df = pd.DataFrame(results['sentiment'])
        
        positive = len(df[df['compound'] > 0.05])
        negative = len(df[df['compound'] < -0.05])
        neutral = len(df[(df['compound'] >= -0.05) & (df['compound'] <= 0.05)])
        total = len(df)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Analyzed", total)
        col2.metric("Positive 😊", positive, f"{positive/total*100:.1f}%")
        col3.metric("Neutral 😐", neutral, f"{neutral/total*100:.1f}%")
        col4.metric("Negative 😞", negative, f"{negative/total*100:.1f}%")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig, ax = plt.subplots(figsize=(8, 6))
            labels = ['Positive', 'Negative', 'Neutral']
            sizes = [positive, negative, neutral]
            colors = ['#2ecc71', '#e74c3c', '#95a5a6']
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)
            plt.close()
        
        with col2:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(df['compound'], bins=30, color='steelblue', edgecolor='white', alpha=0.7)
            ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Neutral')
            ax.axvline(x=df['compound'].mean(), color='green', linestyle='--', 
                      linewidth=2, label=f'Mean: {df["compound"].mean():.3f}')
            ax.set_xlabel('Sentiment Score (-1 to +1)')
            ax.set_ylabel('Frequency')
            ax.legend()
            st.pyplot(fig)
            plt.close()
    
    # 4. Readability
    if show_readability and results['readability']:
        st.markdown('<div class="section-header">📖 Readability</div>', unsafe_allow_html=True)
        
        r = results['readability']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Flesch Reading Ease", f"{r['flesch_score']:.1f}")
            if r['flesch_score'] >= 90:
                st.info("📘 Very Easy (5th grade)")
            elif r['flesch_score'] >= 80:
                st.info("📗 Easy (6th grade)")
            elif r['flesch_score'] >= 70:
                st.info("📙 Fairly Easy (7th grade)")
            elif r['flesch_score'] >= 60:
                st.info("📒 Plain English (8th-9th grade)")
            elif r['flesch_score'] >= 50:
                st.info("📕 Fairly Difficult (10th-12th grade)")
            else:
                st.warning("📖 Difficult (College level)")
        
        with col2:
            st.metric("Flesch-Kincaid Grade", f"{r['fk_score']:.1f}")
            st.caption(f"Total sentences: {r['total_sentences']}")
        
        with col3:
            st.metric("Avg Words/Sentence", f"{r['avg_words']:.1f}")
            st.caption(f"Total words: {r['total_words']}")
    
    # 5. Topic Modeling
    if show_topic and results['topics']:
        st.markdown('<div class="section-header">🎯 Topics Discovered</div>', unsafe_allow_html=True)
        
        topics = results['topics']
        cols = st.columns(min(len(topics), 4))
        
        for i, topic_words in enumerate(topics):
            col_idx = i % len(cols)
            with cols[col_idx]:
                st.markdown(f"""
                <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                            margin: 0.5rem 0; border-left: 4px solid #1f77b4;">
                    <strong>Topic {i+1}</strong>
                    <p style="font-size: 0.9rem; margin-top: 0.5rem; color: #2c3e50;">
                        {', '.join(topic_words[:10])}
                    </p>
                    <small style="color: #6c757d;">
                        Keywords: {', '.join(topic_words[:5])}
                    </small>
                </div>
                """, unsafe_allow_html=True)
    
    # Export functionality
    if 'export_trigger' in st.session_state and st.session_state['export_trigger']:
        with st.spinner("Generating report..."):
            if export_format == "Text Report":
                report_text = generate_text_report(results, filename)
                st.download_button(
                    label="📥 Download Text Report",
                    data=report_text,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            elif export_format == "CSV Data":
                # Create CSV with all data
                csv_data = StringIO()
                csv_data.write("Word,Frequency,Percentage\n")
                for word, freq in results['fdist'].most_common(100):
                    pct = (freq / results['total_words'] * 100)
                    csv_data.write(f"{word},{freq},{pct:.2f}\n")
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data.getvalue(),
                    file_name=f"word_frequency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            elif export_format == "JSON":
                # Create JSON export
                export_data = {
                    'filename': filename,
                    'language': language,
                    'date': datetime.now().isoformat(),
                    'statistics': {
                        'total_words': results['total_words'],
                        'unique_words': results['unique_words'],
                        'sentences_analyzed': len(results['sentiment'])
                    },
                    'top_words': [{'word': w, 'frequency': f} for w, f in results['fdist'].most_common(30)],
                    'topics': results['topics']
                }
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"analysis_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        st.session_state['export_trigger'] = False
        st.success("✅ Report generated! Click download button above.")

else:
    # Welcome
    st.markdown("""
    ## 👈 Welcome to Book Analyzer Pro!
    
    ### 🚀 Features
    - **📁 Multi-format support** - TXT, PDF, DOCX, EPUB
    - **🌍 25+ Languages** - Including Bulgarian, Arabic, Russian, and more
    - **😊 Sentiment Analysis** - Understand emotional tone
    - **📖 Readability Scores** - Measure text complexity
    - **🎯 Topic Modeling** - Discover hidden themes
    - **📤 Export Reports** - Text, CSV, JSON
    
    ### 📖 Quick Start
    1. Upload a file or paste text using the sidebar
    2. Select your language
    3. Customize analysis options
    4. View results and export reports!
    
    ### 🌍 Supported Languages
    English, Bulgarian, Spanish, French, German, Italian, Portuguese,
    Dutch, Russian, Arabic, Turkish, Greek, Swedish, Norwegian, Danish,
    Finnish, Hungarian, Polish, Czech, Romanian, Slovak, Slovenian,
    Estonian, Latvian, Lithuanian
    
    ### 📁 Supported Formats
    - 📄 TXT - Plain text files
    - 📑 PDF - Documents
    - 📝 DOCX - Word documents
    - 📚 EPUB - E-books
    """)
    
    # Sample text option
    try:
        with open('great_expectations.txt', 'r', encoding='utf-8') as f:
            sample_text = f.read()
            st.success("✅ Sample text 'Great Expectations' is available!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📚 Load Sample Text"):
                    # Store in session state
                    st.session_state['sample_text'] = sample_text
                    st.rerun()
            
            with col2:
                st.download_button(
                    label="📥 Download Sample",
                    data=sample_text,
                    file_name="great_expectations.txt",
                    mime="text/plain"
                )
    except:
        st.info("💡 Tip: Upload a .txt, .pdf, .docx, or .epub file to get started!")

# Handle sample load
if 'sample_text' in st.session_state:
    # This will run on next rerun
    pass