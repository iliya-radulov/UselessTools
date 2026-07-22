# Book Analyzer App

```text
Let's build a book analyzer, based on Megan Silvey ipynb  [Build Three Real-World Python Applications] https://github.com/LinkedInLearning/build-three-real-world-python-applications-4379002/tree/main/Chapter%203. I will try to give a step by step description and test each part carefully.
````

We'll start with the basics and build up.
📋 Step 1: Set Up Your Environment

First, let's create a clean project folder and install the dependencies.
1.1 Create Project Folder

Open your terminal/command prompt and run:
```bash
# Create a new folder for your project
mkdir book_analyzer
cd book_analyzer
# Create a folder for the app files
mkdir app_files
# Create a virtual environment (optional but recommended)
python -m venv .venv
# Activate the virtual environment
source .venv/bin/activate 
```

1.2 Create requirements.txt

Create a file called requirements.txt in the book_analyzer folder with this content:

```txt
# requirements.txt
streamlit==1.28.0
nltk==3.8.1
gensim==4.3.1
wordcloud==1.9.2
pandas==2.0.3
matplotlib==3.7.2
Pillow==10.0.0
PyPDF2==3.0.1
python-docx==1.0.0
EbookLib==0.18
beautifulsoup4==4.12.2
lxml==4.9.3
reportlab==4.0.7
fpdf2==2.7.5
stopwordsiso==0.3.5
```

1.3 Install Dependencies

In your terminal, run:
```bash
# Install all dependencies
pip install -r requirements.txt
# Or install individually (if you prefer)
pip install streamlit nltk gensim wordcloud pandas matplotlib Pillow
```


📋 Step 2: Download Sample Text

Let's get the sample text file (Great Expectations) that your notebooks use:
Option A: If you already have the file

Just place great_expectations.txt in your book_analyzer folder.
Option B: Download it from Project Gutenberg

Open Python in your terminal:
```bash

import urllib.request
# Download Great Expectations from Project Gutenberg
url = "https://www.gutenberg.org/files/1400/1400-0.txt"
response = urllib.request.urlopen(url)
text = response.read().decode('utf-8')

# Save to file
with open('great_expectations.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print("File downloaded successfully!")
exit()
```

📋 Step 3: Test Basic Version (Single File)

Now let's create the simplest working version to test. This will be just the basic features from your notebook.

3.1 Create app_basic.py

Create this file in your book_analyzer folder:
```python
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
```

3.2 Run the Basic Version

In your terminal, navigate to the book_analyzer folder and run:
```bash
streamlit run app_basic.py
```
3.3 Test with Your File

    Open the URL shown in terminal (usually http://localhost:8501)

    Upload a .txt file (use great_expectations.txt if you have it)

    Check if you see the statistics and visualizations

    If everything works, great! If not, let me know the error.

📋 Step 4: Add More Features (Version 2)

Now let's add more features from your notebooks. Create app_v2.py:


Test 2: Custom Stopwords (Basic Implementation)

Let's add a simple custom stopword feature. Update the tokenization part in app_v2.py:
```python 
# In app_v2.py, find the tokenization section and replace with:
# Custom stopwords
custom_stopwords = st.sidebar.text_input(
    "Extra stopwords (comma-separated)",
    placeholder="e.g., chapter, introduction"
)

# Tokenize with custom stopwords
tokens = word_tokenize(clean_text)
stop_words = set(stopwords.words('english'))

# Add custom stopwords
if custom_stopwords:
    extra = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
    stop_words.update(extra)

tokens = [word for word in tokens if word not in stop_words]
tokens = [word for word in tokens if len(word) >= 3]
```

📋 Step 6: Troubleshooting Guide

If you encounter issues, here's how to fix them:
Issue 1: "Module not found"
```bash

# Reinstall the module
pip install [module_name] --upgrade

# Example:
pip install streamlit --upgrade
```

Issue 2: NLTK data not founds

# Open Python and download manually
```python
>>> import nltk
>>> nltk.download('all')  # Downloads everything
>>> exit()
```

Issue 3: File encoding errors

```python
# Try different encodings in the read function:
text = uploaded_file.read().decode('utf-8', errors='ignore')
# or
text = uploaded_file.read().decode('latin-1')
```

Issue 4: Streamlit won't start
```bash

# Check if port is in use
streamlit run app_basic.py --server.port 8502
# Or restart Streamlit
# Press Ctrl+C to stop, then run again
```

📋 Step 7: Create a Simple Test Script

Before running the full app, create a test script to verify everything works:

```python
# test_setup.py
# Run this to test if all libraries work

import nltk
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gensim
import ssl

print("Testing imports...")

# Download NLTK data
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')
nltk.download('wordnet')

print("✅ NLTK downloaded")

# Test tokenization
test_text = "This is a test sentence. Let's see if it works."
tokens = word_tokenize(test_text)
print(f"✅ Tokenization works: {tokens[:5]}")

# Test stopwords
stop = stopwords.words('english')
print(f"✅ Stopwords loaded: {len(stop)} words")

# Test sentiment
analyzer = SentimentIntensityAnalyzer()
score = analyzer.polarity_scores("This is great!")
print(f"✅ Sentiment works: {score}")

# Test wordcloud
from wordcloud import WordCloud
wc = WordCloud().generate("test text")
print("✅ WordCloud works")

# Test gensim
from gensim.corpora import Dictionary
dict_test = Dictionary([["test", "text"]])
print("✅ Gensim works")

print("\n🎉 All tests passed! Your environment is ready.")
```

Run it:


```bash
python test_setup.py
```

# 🚀 How to Run

```bash
# Navigate to your project folder
cd book_analyzer
# Run the app
streamlit run app_final.py
```
✨ New Features Added

    📄 Multi-format Support

        PDF reading with PyPDF2

        DOCX with python-docx

        EPUB with EbookLib

    🌍 Extended Languages (25+)

        Bulgarian 🇧🇬

        Russian, Arabic, Turkish, Greek

        Nordic languages (Swedish, Norwegian, Danish, Finnish)

        Eastern European (Polish, Czech, Romanian, Slovak, Slovenian)

        Baltic (Estonian, Latvian, Lithuanian)

        Western European (English, Spanish, French, German, Italian, Portuguese, Dutch)

    📤 Export Reports

        PDF Report with all analysis

        CSV with word frequencies

        JSON with structured data

    🎨 Enhanced UI

        Better statistics display

        Language flags and info

        More intuitive layout



📝 Testing Checklist

Test with different files:

    .txt file (Great Expectations)

    .pdf file (any PDF document)

    .docx file

    .epub file

Test languages:

    Bulgarian text

    Spanish/French/German

    Any other language

Test export:

    PDF Report

    CSV Data

    JSON

📋 Step 8: Next Steps Checklist

Once everything works, let me know which of these you want to implement:

    Multi-file formats (PDF, DOCX, EPUB)

    Multiple languages (Spanish, French, German, etc.)

    Advanced custom stopwords with file upload

    Chapter detection and analysis

    Readability scores

    Comparison mode (compare two books)

    Export reports (PDF, CSV)

    Character analysis

    Timeline visualization


