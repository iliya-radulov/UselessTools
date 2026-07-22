# app_v2.py

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

st.set_page_config(
    page_title="📚 Book Analyzer - V2",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Book Text Analyzer - Version 2 (Fixed)")

# Sidebar with options
st.sidebar.title("⚙️ Options")

# File upload in sidebar
uploaded_file = st.sidebar.file_uploader("Upload a .txt file", type=['txt'])

# Custom stopwords
custom_stopwords = st.sidebar.text_input(
    "Extra stopwords (comma-separated)",
    placeholder="e.g., chapter, introduction, preface"
)

# Analysis options
st.sidebar.subheader("Analysis Features")
show_wordcloud = st.sidebar.checkbox("Word Cloud", value=True)
show_frequency = st.sidebar.checkbox("Word Frequency", value=True)
show_sentiment = st.sidebar.checkbox("Sentiment Analysis", value=True)
show_topic = st.sidebar.checkbox("Topic Modeling", value=False)

if uploaded_file:
    # Read and process text
    with st.spinner("Reading file..."):
        try:
            text = uploaded_file.read().decode('utf-8')
        except:
            text = uploaded_file.read().decode('latin-1')
    
    # Display basic stats
    st.subheader("📊 Document Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Characters", len(text))
    col2.metric("Total Words", len(text.split()))
    col3.metric("Total Sentences", len(text.split('.')))
    
    # Show text preview
    with st.expander("📄 Text Preview"):
        st.text(text[:500] + "..." if len(text) > 500 else text)
    
    # Clean and tokenize
    with st.spinner("Processing text..."):
        # Clean text for word cloud
        clean_text = text.lower()
        clean_text = re.sub("[^a-zA-Z0-9]", " ", clean_text)
        
        # Tokenize
        tokens = word_tokenize(clean_text)
        stop_words = set(stopwords.words('english'))
        
        # Add custom stopwords
        if custom_stopwords:
            extra = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
            stop_words.update(extra)
        
        tokens = [word for word in tokens if word not in stop_words]
        tokens = [word for word in tokens if len(word) >= 3]
        
        st.success(f"✅ Processed {len(tokens)} tokens")
    
    # 1. Word Cloud
    if show_wordcloud:
        st.subheader("☁️ Word Cloud")
        with st.spinner("Generating word cloud..."):
            try:
                wordcloud = WordCloud(
                    max_words=200,
                    background_color='white',
                    random_state=1
                ).generate(clean_text)
                
                fig, ax = plt.subplots(figsize=(14, 8))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.error(f"Error generating word cloud: {e}")
    
    # 2. Word Frequency
    if show_frequency:
        st.subheader("📊 Word Frequency")
        with st.spinner("Analyzing frequency..."):
            try:
                fdist = nltk.FreqDist(tokens)
                
                # Display top words
                top_words = pd.DataFrame(fdist.most_common(20), columns=['Word', 'Frequency'])
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(top_words, use_container_width=True, height=400)
                
                with col2:
                    # FIXED: Create plot manually instead of using fdist.plot()
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    # Get the top 20 words and their frequencies
                    top_20 = fdist.most_common(20)
                    words = [item[0] for item in top_20]
                    freqs = [item[1] for item in top_20]
                    
                    # Create bar chart
                    ax.bar(words, freqs, color='steelblue')
                    ax.set_xlabel('Words')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Top 20 Most Frequent Words')
                    ax.tick_params(axis='x', rotation=45)
                    
                    st.pyplot(fig)
                    plt.close()
            except Exception as e:
                st.error(f"Error in frequency analysis: {e}")
    
    # 3. Sentiment Analysis
    if show_sentiment:
        st.subheader("😊 Sentiment Analysis")
        with st.spinner("Analyzing sentiment..."):
            try:
                analyzer = SentimentIntensityAnalyzer()
                
                # Split into sentences (using simple method for now)
                sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 10]
                
                if not sentences:
                    st.warning("No sentences found for sentiment analysis")
                else:
                    # Analyze sentiment for a sample (first 100 sentences for speed)
                    sample_sentences = sentences[:min(100, len(sentences))]
                    
                    results = []
                    for s in sample_sentences:
                        scores = analyzer.polarity_scores(s)
                        results.append({
                            'sentence': s[:100] + '...' if len(s) > 100 else s,
                            'compound': scores['compound'],
                            'neg': scores['neg'],
                            'neu': scores['neu'],
                            'pos': scores['pos']
                        })
                    
                    df = pd.DataFrame(results)
                    
                    # Show statistics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Sentences", len(df))
                    col2.metric("Positive", len(df[df['compound'] > 0]))
                    col3.metric("Neutral", len(df[df['compound'] == 0]))
                    col4.metric("Negative", len(df[df['compound'] < 0]))
                    
                    # Sentiment distribution
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.hist(df['compound'], bins=30, color='steelblue', edgecolor='white', alpha=0.7)
                    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Neutral')
                    ax.axvline(x=df['compound'].mean(), color='green', linestyle='--', linewidth=2, label=f'Mean: {df["compound"].mean():.2f}')
                    ax.set_xlabel('Sentiment Score')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Sentiment Distribution')
                    ax.legend()
                    st.pyplot(fig)
                    plt.close()
                    
                    # Show average sentiment
                    avg_sentiment = df['compound'].mean()
                    if avg_sentiment > 0.05:
                        sentiment_text = "😊 Generally Positive"
                    elif avg_sentiment < -0.05:
                        sentiment_text = "😞 Generally Negative"
                    else:
                        sentiment_text = "😐 Generally Neutral"
                    
                    st.info(f"**Overall Sentiment**: {sentiment_text} (Average score: {avg_sentiment:.3f})")
                    
                    # Show sample sentences
                    with st.expander("📝 Sample Sentences by Sentiment"):
                        tab1, tab2, tab3 = st.tabs(["😊 Positive", "😐 Neutral", "😞 Negative"])
                        
                        with tab1:
                            positive_samples = df[df['compound'] > 0].head(5)
                            for _, row in positive_samples.iterrows():
                                st.write(f"• {row['sentence']} *(Score: {row['compound']:.2f})*")
                        
                        with tab2:
                            neutral_samples = df[df['compound'] == 0].head(5)
                            for _, row in neutral_samples.iterrows():
                                st.write(f"• {row['sentence']} *(Score: {row['compound']:.2f})*")
                        
                        with tab3:
                            negative_samples = df[df['compound'] < 0].head(5)
                            for _, row in negative_samples.iterrows():
                                st.write(f"• {row['sentence']} *(Score: {row['compound']:.2f})*")
            
            except Exception as e:
                st.error(f"Error in sentiment analysis: {e}")
    
    # 4. Topic Modeling
    if show_topic:
        st.subheader("🎯 Topic Modeling")
        st.info("Topic modeling requires more data and may take a moment...")
        
        with st.spinner("Identifying topics..."):
            try:
                # Prepare data
                sentences_list = [s.strip() for s in text.split('.') if len(s.strip()) > 20]
                
                if len(sentences_list) < 10:
                    st.warning("Not enough sentences for topic modeling (need at least 10)")
                else:
                    # Process for LDA (limit to 200 sentences for speed)
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
                            # Run LDA with 3 topics
                            model = ldamodel.LdaModel(
                                corpus, 
                                id2word=dictionary, 
                                num_topics=3, 
                                passes=10,
                                random_state=1
                            )
                            
                            # Display topics
                            st.subheader("📋 Discovered Topics")
                            topics = model.show_topics(formatted=False)
                            
                            cols = st.columns(3)
                            for i, topic in enumerate(topics):
                                words = [word for word, prob in topic[:10]]
                                prob = [f"{prob:.3f}" for word, prob in topic[:10]]
                                
                                with cols[i]:
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 0.5rem; border-left: 4px solid #1f77b4;">
                                        <strong>Topic {i+1}</strong>
                                        <p style="font-size: 0.9rem; margin-top: 0.5rem;">
                                            {', '.join(words)}
                                        </p>
                                        <small style="color: #6c757d;">
                                            Top words: {', '.join([f'{w} ({p})' for w, p in zip(words[:5], prob[:5])])}
                                        </small>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.warning("Could not create corpus for topic modeling")
            
            except Exception as e:
                st.error(f"Error in topic modeling: {e}")

else:
    st.info("👈 Please upload a .txt file using the sidebar")
    
    # Show sample options
    st.subheader("📖 How to Get Started")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 📁 Upload Your Text
        1. Click "Browse files" in the sidebar
        2. Select a .txt file
        3. Wait for analysis to complete
        
        ### 🔧 Customize Analysis
        - Add custom stopwords
        - Toggle features on/off
        - Adjust parameters
        """)
    
    with col2:
        st.markdown("""
        ### 📚 Sample Texts
        You can download free books from:
        - [Project Gutenberg](https://www.gutenberg.org/)
        - [Internet Archive](https://archive.org/)
        - [Open Library](https://openlibrary.org/)
        
        ### 💡 Tips
        - Longer texts give better results
        - Remove front matter (copyright, table of contents)
        - Try different stopwords for better analysis
        """)
    
    # Option to load Great Expectations if available
    try:
        with open('great_expectations.txt', 'r', encoding='utf-8') as f:
            sample_text = f.read()
            st.success("✅ Sample text 'Great Expectations' is available!")
            
            if st.button("📚 Load Sample Text"):
                # Create a temporary file-like object
                st.session_state['uploaded_file'] = sample_text
                st.rerun()
    except:
        st.info("No sample text found. Upload your own .txt file!")

st.sidebar.markdown("---")
st.sidebar.write("Version 2.0")