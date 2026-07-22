# app_v3_fixed.py
# Complete fixed version with all features

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
import re
import matplotlib.pyplot as plt
import ssl
import numpy as np

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
    except:
        pass

download_nltk_data()

st.set_page_config(
    page_title="📚 Book Analyzer Pro",
    page_icon="📚",
    layout="wide"
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
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📚 Book Text Analyzer Pro</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Controls")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload a .txt file", 
    type=['txt'],
    help="Upload your text file for analysis"
)

# Custom stopwords
st.sidebar.subheader("🔧 Custom Stopwords")
custom_stopwords = st.sidebar.text_input(
    "Extra stopwords (comma-separated)",
    placeholder="e.g., chapter, introduction, preface, volume"
)

# Language selection
st.sidebar.subheader("🌍 Language")
language = st.sidebar.selectbox(
    "Select language",
    ["English", "Spanish", "French", "German", "Italian", "Portuguese"],
    help="Choose the language of your text"
)

# Analysis options
st.sidebar.subheader("📊 Analysis Features")
show_wordcloud = st.sidebar.checkbox("☁️ Word Cloud", value=True)
show_frequency = st.sidebar.checkbox("📊 Word Frequency", value=True)
show_sentiment = st.sidebar.checkbox("😊 Sentiment Analysis", value=True)
show_readability = st.sidebar.checkbox("📖 Readability Scores", value=True)
show_topic = st.sidebar.checkbox("🎯 Topic Modeling", value=False)

if show_topic:
    num_topics = st.sidebar.slider("Number of Topics", 2, 8, 3)

# Advanced options
with st.sidebar.expander("⚡ Advanced Options"):
    max_words = st.slider("Max words in word cloud", 50, 500, 200)
    sample_sentences = st.slider("Sentences to analyze", 50, 500, 100)

# Main content
if uploaded_file:
    # Read file
    with st.spinner("📖 Reading your file..."):
        try:
            text = uploaded_file.read().decode('utf-8')
        except:
            try:
                text = uploaded_file.read().decode('latin-1')
            except:
                text = uploaded_file.read().decode('utf-8', errors='ignore')
    
    # Basic stats
    st.markdown("### 📊 Document Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_chars = len(text)
    total_words = len(text.split())
    total_sentences = len([s for s in text.split('.') if s.strip()])
    total_paragraphs = len([p for p in text.split('\n') if p.strip()])
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{total_chars:,}</h3>
            <small>Characters</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{total_words:,}</h3>
            <small>Words</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{total_sentences:,}</h3>
            <small>Sentences</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{total_paragraphs:,}</h3>
            <small>Paragraphs</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Preview
    with st.expander("📄 Text Preview (first 500 characters)"):
        st.text(text[:500] + "..." if len(text) > 500 else text)
    
    # Process text
    with st.spinner("⚙️ Processing text..."):
        # Clean text
        clean_text = text.lower()
        clean_text = re.sub("[^a-zA-Z0-9\\s]", " ", clean_text)
        
        # Tokenize
        tokens = word_tokenize(clean_text)
        
        # Get stopwords based on language
        try:
            if language == "English":
                stop_words = set(stopwords.words('english'))
            elif language == "Spanish":
                stop_words = set(stopwords.words('spanish'))
            elif language == "French":
                stop_words = set(stopwords.words('french'))
            elif language == "German":
                stop_words = set(stopwords.words('german'))
            elif language == "Italian":
                stop_words = set(stopwords.words('italian'))
            elif language == "Portuguese":
                stop_words = set(stopwords.words('portuguese'))
            else:
                stop_words = set(stopwords.words('english'))
        except:
            stop_words = set(stopwords.words('english'))
        
        # Add custom stopwords
        if custom_stopwords:
            extra = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
            stop_words.update(extra)
        
        # Filter tokens
        tokens = [word for word in tokens if word not in stop_words]
        tokens = [word for word in tokens if len(word) >= 3]
        
        # Get sentences for sentiment
        sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
        sentences = sentences[:sample_sentences]  # Limit for performance
        
        if not sentences:
            sentences = [text[:500]]  # Fallback
        
        st.success(f"✅ Processed {len(tokens)} tokens and {len(sentences)} sentences")
    
    # 1. Word Cloud
    if show_wordcloud:
        st.markdown('<div class="section-header">☁️ Word Cloud</div>', unsafe_allow_html=True)
        with st.spinner("🎨 Generating word cloud..."):
            try:
                if len(clean_text.strip()) > 10:
                    wordcloud = WordCloud(
                        max_words=max_words,
                        background_color='white',
                        random_state=1,
                        colormap='viridis'
                    ).generate(clean_text)
                    
                    fig, ax = plt.subplots(figsize=(14, 8))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                    plt.close()
                else:
                    st.warning("Text too short for word cloud")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # 2. Word Frequency
    if show_frequency:
        st.markdown('<div class="section-header">📊 Word Frequency Analysis</div>', unsafe_allow_html=True)
        with st.spinner("📊 Analyzing frequency..."):
            try:
                fdist = nltk.FreqDist(tokens)
                
                if len(fdist) > 0:
                    # Top words table
                    top_words = pd.DataFrame(fdist.most_common(30), columns=['Word', 'Frequency'])
                    top_words['Percentage'] = (top_words['Frequency'] / len(tokens) * 100).round(2)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.dataframe(top_words, use_container_width=True, height=400)
                    
                    with col2:
                        # Bar chart
                        top_20 = fdist.most_common(20)
                        words = [item[0] for item in top_20]
                        freqs = [item[1] for item in top_20]
                        
                        fig, ax = plt.subplots(figsize=(10, 6))
                        bars = ax.bar(words, freqs, color='steelblue')
                        ax.set_xlabel('Words')
                        ax.set_ylabel('Frequency')
                        ax.set_title('Top 20 Most Frequent Words')
                        ax.tick_params(axis='x', rotation=45)
                        
                        # Add value labels
                        for bar, freq in zip(bars, freqs):
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height,
                                    f'{freq}', ha='center', va='bottom', fontsize=9)
                        
                        st.pyplot(fig)
                        plt.close()
                    
                    # Additional stats
                    st.markdown("#### 📋 Vocabulary Statistics")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Unique Words", len(fdist))
                    col2.metric("Type-Token Ratio", f"{len(fdist)/len(tokens):.3f}")
                    col3.metric("Most Common", fdist.most_common(1)[0][0] if fdist else "N/A")
                else:
                    st.warning("No tokens found for frequency analysis")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # 3. Sentiment Analysis
    if show_sentiment:
        st.markdown('<div class="section-header">😊 Sentiment Analysis</div>', unsafe_allow_html=True)
        with st.spinner("🔍 Analyzing sentiment..."):
            try:
                analyzer = SentimentIntensityAnalyzer()
                
                # Analyze each sentence
                results = []
                for s in sentences[:sample_sentences]:
                    if len(s.strip()) > 5:
                        scores = analyzer.polarity_scores(s)
                        results.append({
                            'sentence': s[:150] + '...' if len(s) > 150 else s,
                            'compound': scores['compound'],
                            'neg': scores['neg'],
                            'neu': scores['neu'],
                            'pos': scores['pos']
                        })
                
                if results:
                    df = pd.DataFrame(results)
                    
                    # Stats
                    positive = len(df[df['compound'] > 0.05])
                    negative = len(df[df['compound'] < -0.05])
                    neutral = len(df[(df['compound'] >= -0.05) & (df['compound'] <= 0.05)])
                    total = len(df)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Analyzed", total)
                    col2.metric("😊 Positive", positive, f"{positive/total*100:.1f}%")
                    col3.metric("😐 Neutral", neutral, f"{neutral/total*100:.1f}%")
                    col4.metric("😞 Negative", negative, f"{negative/total*100:.1f}%")
                    
                    # Charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Pie chart
                        fig, ax = plt.subplots(figsize=(8, 6))
                        labels = ['Positive', 'Negative', 'Neutral']
                        sizes = [positive, negative, neutral]
                        colors = ['#2ecc71', '#e74c3c', '#95a5a6']
                        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                        ax.axis('equal')
                        ax.set_title('Sentiment Distribution')
                        st.pyplot(fig)
                        plt.close()
                    
                    with col2:
                        # Histogram
                        fig, ax = plt.subplots(figsize=(10, 6))
                        ax.hist(df['compound'], bins=30, color='steelblue', edgecolor='white', alpha=0.7)
                        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Neutral')
                        ax.axvline(x=df['compound'].mean(), color='green', linestyle='--', 
                                  linewidth=2, label=f'Mean: {df["compound"].mean():.3f}')
                        ax.set_xlabel('Sentiment Score (-1 to +1)')
                        ax.set_ylabel('Frequency')
                        ax.set_title('Sentiment Score Distribution')
                        ax.legend()
                        st.pyplot(fig)
                        plt.close()
                    
                    # Overall sentiment
                    avg_sentiment = df['compound'].mean()
                    if avg_sentiment > 0.1:
                        sentiment_text = "😊 **Generally Positive**"
                        sentiment_color = "green"
                    elif avg_sentiment < -0.1:
                        sentiment_text = "😞 **Generally Negative**"
                        sentiment_color = "red"
                    else:
                        sentiment_text = "😐 **Generally Neutral**"
                        sentiment_color = "orange"
                    
                    st.markdown(f"""
                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center;">
                        <h4 style="color: {sentiment_color};">Overall Sentiment: {sentiment_text}</h4>
                        <p>Average score: {avg_sentiment:.3f} (range: -1 to +1)</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No sentences could be analyzed")
            except Exception as e:
                st.error(f"Error in sentiment analysis: {e}")
    
    # 4. Readability Scores
    if show_readability:
        st.markdown('<div class="section-header">📖 Readability Analysis</div>', unsafe_allow_html=True)
        with st.spinner("📊 Calculating readability..."):
            try:
                # Simple syllable counter
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
                
                # Split into sentences and words
                sentences_list = [s for s in re.split(r'[.!?]+', text) if s.strip()]
                words_list = [w for w in re.findall(r'\b\w+\b', text) if w.strip()]
                
                if sentences_list and words_list:
                    total_sentences = len(sentences_list)
                    total_words = len(words_list)
                    total_syllables = sum(count_syllables(w) for w in words_list)
                    
                    # Flesch Reading Ease
                    flesch_score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
                    
                    # Flesch-Kincaid Grade
                    fk_score = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59
                    
                    # Average words per sentence
                    avg_words = total_words / total_sentences
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Flesch Reading Ease",
                            f"{flesch_score:.1f}",
                            help="90-100: Very Easy, 60-70: Plain English, 30-50: Difficult"
                        )
                        # Interpret
                        if flesch_score >= 90:
                            st.info("📘 Very Easy (5th grade level)")
                        elif flesch_score >= 80:
                            st.info("📗 Easy (6th grade level)")
                        elif flesch_score >= 70:
                            st.info("📙 Fairly Easy (7th grade level)")
                        elif flesch_score >= 60:
                            st.info("📒 Plain English (8th-9th grade)")
                        elif flesch_score >= 50:
                            st.info("📕 Fairly Difficult (10th-12th grade)")
                        else:
                            st.warning("📖 Difficult (College level)")
                    
                    with col2:
                        st.metric(
                            "Flesch-Kincaid Grade",
                            f"{fk_score:.1f}",
                            help="US grade level required"
                        )
                    
                    with col3:
                        st.metric(
                            "Avg Words/Sentence",
                            f"{avg_words:.1f}",
                            help="Average sentence length"
                        )
                    
                    st.caption("💡 **Tip**: Aim for Flesch 60-70 for general audiences. Lower score = harder to read.")
                else:
                    st.warning("Not enough text for readability analysis")
            except Exception as e:
                st.error(f"Error calculating readability: {e}")
    
    # 5. Topic Modeling
    if show_topic:
        st.markdown('<div class="section-header">🎯 Topic Modeling</div>', unsafe_allow_html=True)
        with st.spinner(f"🔍 Identifying {num_topics} topics..."):
            try:
                # Prepare sentences for topic modeling
                sentences_list = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
                
                if len(sentences_list) < 10:
                    st.warning("Not enough sentences for topic modeling (need at least 10)")
                else:
                    # Process for LDA (limit for performance)
                    processed_data = []
                    for s in sentences_list[:200]:
                        words = word_tokenize(s.lower())
                        words = [w for w in words if w.isalpha()]
                        words = [w for w in words if w not in stop_words]
                        words = [w for w in words if len(w) >= 3]
                        if words:
                            processed_data.append(words)
                    
                    if len(processed_data) < 10:
                        st.warning("Not enough processed data for topic modeling")
                    else:
                        # Create dictionary and corpus
                        dictionary = Dictionary(processed_data)
                        # Filter extremes
                        dictionary.filter_extremes(no_below=2, no_above=0.5)
                        corpus = [dictionary.doc2bow(text) for text in processed_data]
                        
                        if len(corpus) > 0 and len(dictionary) > 0:
                            # Run LDA
                            model = ldamodel.LdaModel(
                                corpus, 
                                id2word=dictionary, 
                                num_topics=num_topics, 
                                passes=10,
                                random_state=1
                            )
                            
                            # Display topics
                            topics = model.show_topics(formatted=False)
                            
                            # Create columns for topics
                            cols = st.columns(min(num_topics, 4))
                            
                            for i, topic_data in enumerate(topics):
                                # FIXED: Handle different return formats
                                if isinstance(topic_data, tuple) and len(topic_data) >= 2:
                                    topic_id = topic_data[0]
                                    topic_words = topic_data[1]
                                else:
                                    topic_id = i
                                    topic_words = topic_data if isinstance(topic_data, list) else []
                                
                                # Extract words with probabilities
                                word_list = []
                                prob_list = []
                                if isinstance(topic_words, list) and len(topic_words) > 0:
                                    for item in topic_words:
                                        if isinstance(item, tuple) and len(item) >= 2:
                                            word_list.append(item[0])
                                            prob_list.append(item[1])
                                        elif isinstance(item, str):
                                            # Handle string format
                                            word_list.append(item)
                                
                                if not word_list:
                                    word_list = [f"word_{j}" for j in range(5)]
                                
                                col_idx = i % len(cols)
                                with cols[col_idx]:
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; 
                                                margin: 0.5rem 0; border-left: 4px solid #1f77b4;">
                                        <strong>Topic {i+1}</strong>
                                        <p style="font-size: 0.9rem; margin-top: 0.5rem; color: #2c3e50;">
                                            {', '.join(word_list[:10])}
                                        </p>
                                        <small style="color: #6c757d;">
                                            Keywords: {', '.join(word_list[:5])}
                                        </small>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Show topic distribution
                            with st.expander("📊 Topic Distribution Details"):
                                # Get topic distribution for each document
                                topic_distributions = []
                                for doc in corpus[:20]:  # Sample first 20 docs
                                    dist = model.get_document_topics(doc)
                                    topic_distributions.append(dist)
                                
                                # Show example
                                st.write("**Sample topic assignments:**")
                                for i, dist in enumerate(topic_distributions[:5]):
                                    topics_str = ", ".join([f"Topic {t}: {p:.2f}" for t, p in dist if p > 0.1])
                                    st.write(f"Document {i+1}: {topics_str if topics_str else 'Mixed topics'}")
                        else:
                            st.warning("Could not create corpus for topic modeling")
            except Exception as e:
                st.error(f"Error in topic modeling: {str(e)}")
                st.info("💡 Try with a longer text or reduce the number of topics")

else:
    # Welcome screen
    st.markdown("""
    ### 👈 Welcome to Book Text Analyzer Pro!
    
    **Upload a text file using the sidebar to get started.**
    
    #### 🚀 Features:
    - 📊 **Word Cloud** - Visualize the most frequent words
    - 📈 **Word Frequency** - See which words are used most often
    - 😊 **Sentiment Analysis** - Understand the emotional tone
    - 📖 **Readability Scores** - Measure text complexity
    - 🎯 **Topic Modeling** - Discover hidden themes
    
    #### 📁 Supported Formats:
    - ✅ Plain text (.txt)
    
    #### 🔧 Customization:
    - Add your own stopwords
    - Choose from multiple languages
    - Adjust analysis parameters
    
    #### 💡 Try it with:
    - Novels and books
    - Articles and essays
    - Reports and documents
    - Any text you want to analyze!
    """)
    
    # Check for sample file
    try:
        with open('great_expectations.txt', 'r', encoding='utf-8') as f:
            sample_text = f.read()
            st.success("✅ Sample text 'Great Expectations' is available!")
            
            # Create a download button for the sample
            st.download_button(
                label="📚 Download Great Expectations",
                data=sample_text,
                file_name="great_expectations.txt",
                mime="text/plain"
            )
    except:
        st.info("No sample text found. Upload your own .txt file!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Version:** 3.0  
**Made with:** ❤️  
**Powered by:** Streamlit, NLTK, Gensim
""")

# Help section
with st.sidebar.expander("❓ Help"):
    st.markdown("""
    **How to use:**
    1. Upload a .txt file
    2. Select analysis options
    3. View results!
    
    **Tips:**
    - Longer texts give better results
    - Add custom stopwords to remove common words
    - Try different settings for best results
    - Topic modeling works best with 100+ sentences
    
    **Need help?**
    Check the error messages and adjust settings
    """)