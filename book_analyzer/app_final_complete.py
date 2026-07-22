# app_final_complete.py
# Complete Book Analyzer - All features working

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
import os
from io import BytesIO, StringIO
import base64
from datetime import datetime
import json

# Optional: covers many languages NLTK's stopwords corpus doesn't have
# (Bulgarian, Polish, Czech, Slovak, Estonian, Latvian, Lithuanian, etc.)
try:
    import stopwordsiso
    STOPWORDSISO_AVAILABLE = True
except ImportError:
    STOPWORDSISO_AVAILABLE = False

# File format imports
import PyPDF2
import docx
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# Try to import reportlab with proper error handling
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    # Define fallback colors if reportlab not available
    class Colors:
        def __init__(self):
            self.blue = None
            self.grey = None
            self.whitesmoke = None
            self.black = None
            self.beige = None
            self.red = None
            self.green = None
    colors = Colors()

# Language configuration
# 'nltk_stopwords' = fileid NLTK actually uses (note: NLTK uses "slovene", not "slovenian")
# 'iso' = ISO 639-1 code used by stopwordsiso for languages NLTK doesn't cover at all
LANGUAGES = {
    'English': {'code': 'en', 'nltk_stopwords': 'english', 'iso': 'en', 'flag': '🇬🇧'},
    'Bulgarian': {'code': 'bg', 'nltk_stopwords': None, 'iso': 'bg', 'flag': '🇧🇬'},
    'Spanish': {'code': 'es', 'nltk_stopwords': 'spanish', 'iso': 'es', 'flag': '🇪🇸'},
    'French': {'code': 'fr', 'nltk_stopwords': 'french', 'iso': 'fr', 'flag': '🇫🇷'},
    'German': {'code': 'de', 'nltk_stopwords': 'german', 'iso': 'de', 'flag': '🇩🇪'},
    'Italian': {'code': 'it', 'nltk_stopwords': 'italian', 'iso': 'it', 'flag': '🇮🇹'},
    'Portuguese': {'code': 'pt', 'nltk_stopwords': 'portuguese', 'iso': 'pt', 'flag': '🇵🇹'},
    'Dutch': {'code': 'nl', 'nltk_stopwords': 'dutch', 'iso': 'nl', 'flag': '🇳🇱'},
    'Russian': {'code': 'ru', 'nltk_stopwords': 'russian', 'iso': 'ru', 'flag': '🇷🇺'},
    'Arabic': {'code': 'ar', 'nltk_stopwords': 'arabic', 'iso': 'ar', 'flag': '🇸🇦'},
    'Turkish': {'code': 'tr', 'nltk_stopwords': 'turkish', 'iso': 'tr', 'flag': '🇹🇷'},
    'Greek': {'code': 'el', 'nltk_stopwords': 'greek', 'iso': 'el', 'flag': '🇬🇷'},
    'Swedish': {'code': 'sv', 'nltk_stopwords': 'swedish', 'iso': 'sv', 'flag': '🇸🇪'},
    'Norwegian': {'code': 'no', 'nltk_stopwords': 'norwegian', 'iso': 'no', 'flag': '🇳🇴'},
    'Danish': {'code': 'da', 'nltk_stopwords': 'danish', 'iso': 'da', 'flag': '🇩🇰'},
    'Finnish': {'code': 'fi', 'nltk_stopwords': 'finnish', 'iso': 'fi', 'flag': '🇫🇮'},
    'Hungarian': {'code': 'hu', 'nltk_stopwords': 'hungarian', 'iso': 'hu', 'flag': '🇭🇺'},
    'Polish': {'code': 'pl', 'nltk_stopwords': None, 'iso': 'pl', 'flag': '🇵🇱'},
    'Czech': {'code': 'cs', 'nltk_stopwords': None, 'iso': 'cs', 'flag': '🇨🇿'},
    'Romanian': {'code': 'ro', 'nltk_stopwords': 'romanian', 'iso': 'ro', 'flag': '🇷🇴'},
    'Slovak': {'code': 'sk', 'nltk_stopwords': None, 'iso': 'sk', 'flag': '🇸🇰'},
    'Slovenian': {'code': 'sl', 'nltk_stopwords': 'slovene', 'iso': 'sl', 'flag': '🇸🇮'},
    'Estonian': {'code': 'et', 'nltk_stopwords': None, 'iso': 'et', 'flag': '🇪🇪'},
    'Latvian': {'code': 'lv', 'nltk_stopwords': None, 'iso': 'lv', 'flag': '🇱🇻'},
    'Lithuanian': {'code': 'lt', 'nltk_stopwords': None, 'iso': 'lt', 'flag': '🇱🇹'},
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
        # NOTE: there is no such thing as separate 'stopwords_spanish',
        # 'stopwords_bulgarian', etc. packages on the NLTK index - the single
        # 'stopwords' download above already contains every language NLTK ships.
        # (Bulgarian, Polish, Czech, Slovak, Estonian, Latvian and Lithuanian
        # aren't included at all - those are covered via stopwordsiso instead,
        # see get_stopwords_for_language().)
    except:
        pass

download_nltk_data()


def get_stopwords_for_language(language, custom_stopwords=None):
    """Return a stopword set for the given language, combining NLTK (where
    available) with stopwordsiso (which covers languages NLTK doesn't, like
    Bulgarian, Polish, Czech, Slovak, Estonian, Latvian, Lithuanian)."""
    info = LANGUAGES.get(language, LANGUAGES['English'])
    stop_words = set()

    nltk_name = info.get('nltk_stopwords')
    if nltk_name:
        try:
            if nltk_name in stopwords.fileids():
                stop_words |= set(stopwords.words(nltk_name))
        except LookupError:
            pass

    if STOPWORDSISO_AVAILABLE:
        iso_code = info.get('iso')
        try:
            if iso_code and stopwordsiso.has_lang(iso_code):
                stop_words |= set(stopwordsiso.stopwords(iso_code))
        except Exception:
            pass

    if not stop_words:
        # last-resort fallback so analysis still runs, but warn the caller
        stop_words = set(stopwords.words('english'))

    if custom_stopwords:
        extra = [w.strip().lower() for w in custom_stopwords.split(',') if w.strip()]
        stop_words.update(extra)

    return stop_words

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
    """Improved PDF reader that handles non-English text better"""
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        total_pages = len(pdf_reader.pages)
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if not page_text or len(page_text.strip()) < 10:
                    try:
                        page_text = page.extract_text(extraction_mode="layout")
                    except:
                        pass
                
                text += page_text + "\n"
                
            except Exception as e:
                continue
        
        # If we got very little text, try a different approach
        if len(text.strip()) < 100 and total_pages > 1:
            try:
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            except:
                pass
        
        return text
    except Exception as e:
        return ""

def read_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
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

    stop_words = get_stopwords_for_language(language, custom_stopwords)
    
    # Clean text - preserve non-English characters
    clean_text = text.lower()
    clean_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁъЪюЮяЯіІїЇєЄґҐ\s]', ' ', clean_text)
    
    # Tokenize
    tokens = word_tokenize(clean_text)
    tokens = [word for word in tokens if word not in stop_words]
    tokens = [word for word in tokens if len(word) >= 2]
    
    # Word frequency
    fdist = nltk.FreqDist(tokens)
    
    # Get sentences
    sentence_endings = r'[.!?…।।॥？！]'
    sentences = [s.strip() for s in re.split(sentence_endings, text) if len(s.strip()) > 5]
    
    # Sentiment analysis
    sentiment_results = []
    if sentences and language == 'English':
        try:
            analyzer = SentimentIntensityAnalyzer()
            for s in sentences[:200]:
                scores = analyzer.polarity_scores(s)
                sentiment_results.append({
                    'sentence': s[:200],
                    'compound': scores['compound'],
                    'neg': scores['neg'],
                    'neu': scores['neu'],
                    'pos': scores['pos']
                })
        except:
            pass
    elif sentences:
        # Simple fallback for non-English
        positive_words = {'good', 'great', 'excellent', 'wonderful', 'amazing', 'happy', 'love', 'beautiful'}
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'sad', 'hate', 'ugly', 'poor'}
        
        for s in sentences[:200]:
            words = set(word_tokenize(s.lower()))
            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)
            compound = 0
            if pos_count + neg_count > 0:
                compound = (pos_count - neg_count) / (pos_count + neg_count)
            sentiment_results.append({
                'sentence': s[:200],
                'compound': compound,
                'neg': neg_count / max(1, (pos_count + neg_count)),
                'neu': 1.0,
                'pos': pos_count / max(1, (pos_count + neg_count))
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
                words = [w for w in words if len(w) >= 2]
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
                vowels = "aeiouyаеиоуыэюяіїє"
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
            total_syllables = sum(count_syllables(w) for w in tokens[:1000])
            
            if total_sentences > 0 and total_words > 0 and total_syllables > 0:
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


def get_unicode_font_name():
    """Register (once) and return a font name that can render Cyrillic,
    Greek, and other non-Latin scripts in ReportLab PDFs.

    Primary source: the DejaVu Sans font bundled with matplotlib, which is
    guaranteed to be present wherever matplotlib is installed and covers
    Cyrillic/Greek/Latin-Extended glyphs. Falls back to a short list of
    common system font paths, then finally to Helvetica (Latin-only)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if 'UnicodeFont' in pdfmetrics.getRegisteredFontNames():
        return 'UnicodeFont'

    font_paths = []

    # matplotlib ships its own copy of DejaVu Sans - use that first, it's
    # the most reliable cross-platform source of full Unicode coverage.
    try:
        from matplotlib import font_manager
        mpl_font = font_manager.findfont('DejaVu Sans', fallback_to_default=True)
        if mpl_font and os.path.exists(mpl_font):
            font_paths.append(mpl_font)
    except Exception:
        pass

    # Common system font locations as a secondary fallback.
    font_paths += [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/arialuni.ttf',
        '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
        '/System/Library/Fonts/Supplemental/Arial.ttf',
    ]

    for font_path in font_paths:
        try:
            if font_path and os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('UnicodeFont', font_path))
                return 'UnicodeFont'
        except Exception:
            continue

    # Nothing worked - Cyrillic/Greek text will not render correctly.
    return 'Helvetica'


def generate_pdf_report(text, results, filename):
    """Generate PDF report with proper Unicode support for all languages"""
    if not REPORTLAB_AVAILABLE:
        return None

    try:
        font_name = get_unicode_font_name()

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create custom styles with Unicode font
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=colors.blue,
            spaceAfter=30,
            fontName=font_name
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=12,
            fontName=font_name
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            fontName=font_name
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Book Analysis Report", title_style))
        story.append(Spacer(1, 12))
        
        # Info
        story.append(Paragraph(f"File: {filename}", normal_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
        story.append(Spacer(1, 12))
        
        # Statistics
        story.append(Paragraph("Document Statistics", heading_style))
        
        # Prepare statistics data with proper escaping
        stats_data = [
            ['Metric', 'Value'],
            ['Total Words', str(results['total_words'])],
            ['Unique Words', str(results['unique_words'])],
            ['Sentences Analyzed', str(len(results['sentiment']))],
        ]
        
        if results['readability']:
            stats_data.append(['Flesch Reading Ease', f"{results['readability']['flesch_score']:.1f}"])
            stats_data.append(['Flesch-Kincaid Grade', f"{results['readability']['fk_score']:.1f}"])
            stats_data.append(['Avg Words/Sentence', f"{results['readability']['avg_words']:.1f}"])
        
        table = Table(stats_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Top words
        if results['fdist']:
            story.append(Paragraph("Top 20 Words", heading_style))
            top_words = results['fdist'].most_common(20)
            word_data = [['Word', 'Frequency']]
            for word, freq in top_words:
                # Escape any special characters in the word
                try:
                    word_str = str(word)
                except:
                    word_str = repr(word)
                word_data.append([word_str, str(freq)])
            
            word_table = Table(word_data)
            word_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(word_table)
            story.append(Spacer(1, 20))
        
        # Sentiment
        if results['sentiment']:
            story.append(Paragraph("Sentiment Analysis", heading_style))
            df = pd.DataFrame(results['sentiment'])
            positive = len(df[df['compound'] > 0.05])
            negative = len(df[df['compound'] < -0.05])
            neutral = len(df[(df['compound'] >= -0.05) & (df['compound'] <= 0.05)])
            
            sent_data = [
                ['Sentiment', 'Count', 'Percentage'],
                ['Positive', str(positive), f"{positive/len(df)*100:.1f}%"],
                ['Negative', str(negative), f"{negative/len(df)*100:.1f}%"],
                ['Neutral', str(neutral), f"{neutral/len(df)*100:.1f}%"],
            ]
            sent_table = Table(sent_data)
            sent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(sent_table)
            story.append(Spacer(1, 20))
            
            # Add sentiment interpretation
            avg_sentiment = df['compound'].mean()
            if avg_sentiment > 0.05:
                sentiment_text = "Positive"
            elif avg_sentiment < -0.05:
                sentiment_text = "Negative"
            else:
                sentiment_text = "Neutral"
            story.append(Paragraph(f"Overall Sentiment: {sentiment_text} (Average: {avg_sentiment:.3f})", normal_style))
            story.append(Spacer(1, 10))
        
        # Topics
        if results['topics']:
            story.append(Paragraph("Topics Discovered", heading_style))
            for i, topic in enumerate(results['topics']):
                topic_text = ', '.join(topic[:10])
                # Escape special characters
                try:
                    topic_text = str(topic_text)
                except:
                    topic_text = repr(topic_text)
                story.append(Paragraph(f"Topic {i+1}: {topic_text}", normal_style))
                story.append(Spacer(1, 6))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

# Simple text report
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
    stopword_source = "NLTK" if lang_info['nltk_stopwords'] else ("stopwordsiso" if STOPWORDSISO_AVAILABLE else "none available")
    st.caption(f"Code: {lang_info['code']} | Stopwords source: {stopword_source}")
    if not lang_info['nltk_stopwords'] and not STOPWORDSISO_AVAILABLE:
        st.warning("⚠️ Install `stopwordsiso` (pip install stopwordsiso) for stopword support in this language.")
    
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

# Export options
with st.sidebar.expander("📤 Export", expanded=False):
    st.markdown("Download analysis results:")
    export_format = st.selectbox("Format", ["Text Report", "CSV Data", "JSON", "PDF Report"])
    
    if export_format == "PDF Report" and not REPORTLAB_AVAILABLE:
        st.warning("⚠️ PDF export requires ReportLab. Install with: pip install reportlab")
    
    if st.button("📥 Generate Report"):
        st.session_state['export_trigger'] = True

# Language stats
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Supported Languages (25+):**  
🇬🇧 English 🇧🇬 Bulgarian 🇪🇸 Spanish 🇫🇷 French  
🇩🇪 German 🇮🇹 Italian 🇵🇹 Portuguese 🇳🇱 Dutch  
🇷🇺 Russian 🇸🇦 Arabic 🇹🇷 Turkish 🇬🇷 Greek  
🇸🇪 Swedish 🇳🇴 Norwegian 🇩🇰 Danish 🇫🇮 Finnish  
🇭🇺 Hungarian 🇵🇱 Polish 🇨🇿 Czech 🇷🇴 Romanian  
🇸🇰 Slovak 🇸🇮 Slovenian 🇪🇪 Estonian 🇱🇻 Latvian 🇱🇹 Lithuanian
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**Version:** 4.3 | Made with ❤️")

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
            
            # Show file info
            file_size = len(text)
            st.info(f"📄 File: {filename} | Size: {file_size:,} characters")
            
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
                    colormap='viridis',
                    width=800,
                    height=400
                ).generate(results['clean_text'])
                
                fig, ax = plt.subplots(figsize=(14, 8))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
                plt.close()
            except Exception as e:
                st.error(f"Error generating word cloud: {e}")
    
    # 2. Word Frequency - FIXED: Replaced use_container_width with width
    if show_frequency and results['fdist']:
        st.markdown('<div class="section-header">📊 Word Frequency</div>', unsafe_allow_html=True)
        
        fdist = results['fdist']
        top_words = pd.DataFrame(fdist.most_common(30), columns=['Word', 'Frequency'])
        top_words['Percentage'] = (top_words['Frequency'] / results['total_words'] * 100).round(2)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(top_words, width='stretch', height=400)  # FIXED: use width instead of use_container_width
        
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
            colors_pie = ['#2ecc71', '#e74c3c', '#95a5a6']
            ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
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
            if export_format == "PDF Report":
                if REPORTLAB_AVAILABLE:
                    pdf_buffer = generate_pdf_report(text, results, filename)
                    if pdf_buffer:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_buffer,
                            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error("Failed to generate PDF report")
                else:
                    st.error("PDF export requires ReportLab. Install with: pip install reportlab")
            
            elif export_format == "Text Report":
                report_text = generate_text_report(results, filename)
                st.download_button(
                    label="📥 Download Text Report",
                    data=report_text,
                    file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
            
            elif export_format == "CSV Data":
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
    - **📤 Export Reports** - Text, CSV, JSON, PDF
    
    ### 📖 Quick Start
    1. Upload a file or paste text using the sidebar
    2. Select your language
    3. Customize analysis options
    4. View results and export reports!
    """)
    
    # Sample text option
    try:
        with open('great_expectations.txt', 'r', encoding='utf-8') as f:
            sample_text = f.read()
            st.success("✅ Sample text 'Great Expectations' is available!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📚 Load Sample Text"):
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
    # Clear the session state after loading
    if not uploaded_file and not direct_text:
        st.session_state.pop('sample_text')
        st.rerun()
