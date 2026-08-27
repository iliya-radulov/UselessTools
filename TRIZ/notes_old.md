This was meant to be a fun project to explore the principles of TRIZ and how they can be applied to problem-solving and innovation. The goal was not exactly clear, so the results is actually surprisingly good. I learned how to set a small local Ollama based RAG system and how to use it to generate ideas and solutions based on TRIZ principles. 

```text
Now (M4 Mac)
└── Install Ollama
└── Test TRIZ prompts with local models
└── Build RAG prototype with LlamaIndex


Next (RTX 5060)
└── Fine-tune Llama 8B on TRIZ dataset
└── Run RAG with Mistral 7B
└── Use quantized models for larger LLMs
```

## Step 1: Install Ollama

```bash
# Install Ollama
brew install ollama

# Pull a model
ollama pull llama3.1

#install the python packages
pip3 install llama-index llama-index-llms-ollama llama-index-embeddings-ollama

# Test it
ollama run llama3.1
``` 

## Step 2: Test Ollama:

```bash
# Start Ollama in background:

ollama serve

# open a new terminal and run the following command to test the model:
ollama run llama3.1 --prompt "What are the 40 TRIZ principles?"
```

## Step 3: Create Project Folder

```bash
# Create a project folder
mkdir triz-rag
cd triz-rag
mkdir documents
# copy the TRIZ documents into the documents folder
```

## Step 3b: IF documents are not in PDF format, convert them using `calibre` or `djvulibre` or other tools:

```bash
# For EPUB and DJVU conversion
brew install calibre
ebook-convert Pelevin_t.172341.fb2.epub pelevin_t.pdf

# Convert all EPUBs at once
for f in ~/pelevin-epub/*.epub; do
    ebook-convert "$f" "${f%.epub}.pdf"
    echo "Converted: $f"
done

# convert fb2 to PDF
brew install fb2pdf
fb2pdf yourbook.fb2 yourbook.pdf
for f in ~/pelevin-fb2/*.fb2; do
    fb2pdf "$f" "${f%.fb2}.pdf"
    echo "Converted: $f"
done

# For DJVU specifically
brew install djvulibre
ddjvu -format=pdf yourbook.djvu yourbook.pdf

# To convert DOC to PDF:
brew install libreoffice
libreoffice --convert-to pdf yourfile.doc

# To convert audio books to text, you can use `ffmpeg` and `whisper`:
# Install Whisper (OpenAI's speech to text)
pip3 install openai-whisper

# Install ffmpeg for audio processing
brew install ffmpeg

# for single audio file:
whisper audiobook.mp3 --language Russian --output_format txt

# for batch processing:
for f in ~/pelevin-audio/*.mp3; do
    whisper "$f" --language Russian --output_format txt
    echo "Done: $f"
done  
```

## Step 4: Create a RAG Script

```bash
# Make sure you're in the project folder
cd ~/triz-rag# 

# Check your folder structure looks like this
ls ~/triz-rag/documents/
# Should show your 3 PDF files

# Create the script
nano triz_rag.py
```
## THIS IS THE FINAL VERSION OF THE SCRIPT
## old versions can be found at the bottom of this file as reference.


```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import os
import json

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
INDEX_PATH     = "./storage"
TRACKED_FILES  = "./storage/indexed_files.json"  # ✅ tracks what's indexed
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0
DIVIDER        = "-" * 50
EXIT_COMMANDS  = ['exit', 'quit', 'q', 'bye', 'пока', 'выход']
# ───────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Viktor Pelevin expert assistant with access to 
his complete works in Russian — 91 books including novels, 
short stories and essays spanning his entire career from 
early works to the complete Transhumanism series.

Your responsibilities:
- Answer ALL questions about Pelevin's books and themes
- Reference specific books and characters in your answers
- Discuss recurring themes: consciousness, Buddhism, reality,
  Soviet/post-Soviet life, identity, simulation, emptiness
- Answer in the same language the question is asked
  (Russian question = Russian answer, English = English)
- Be literary, philosophical and thoughtful
- Never refuse a question about Pelevin or his works
- When quoting, mention which book it is from

Always base answers on the provided Pelevin documents.
"""

def setup():
    print("Setting up models...")
    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=TIMEOUT,
        context_window=4096,
        system_prompt=SYSTEM_PROMPT
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    print("Models ready!")

# ── File Tracking ──────────────────────────────

def load_tracked_files():
    """Load list of already indexed files"""
    if os.path.exists(TRACKED_FILES):
        with open(TRACKED_FILES, 'r') as f:
            return set(json.load(f))
    return set()

def save_tracked_files(tracked):
    """Save list of indexed files"""
    with open(TRACKED_FILES, 'w') as f:
        json.dump(list(tracked), f, indent=2)

def get_new_files(tracked_files):
    """Find files in documents folder not yet indexed"""
    all_files = set(
        f for f in os.listdir(DOCUMENTS_PATH)
        if f.endswith('.pdf')
    )
    new_files = all_files - tracked_files
    return new_files

# ── Index Management ───────────────────────────

def build_fresh_index():
    """Build index from scratch — first time only"""
    print("Loading all Pelevin documents...")
    documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
    print(f"Loaded {len(documents)} document chunks")
    print("Building index (first time only)...")

    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    index.storage_context.persist(persist_dir=INDEX_PATH)

    # ✅ Track all indexed files
    all_files = set(os.listdir(DOCUMENTS_PATH))
    save_tracked_files(all_files)
    print(f"Index built and saved! {len(all_files)} files tracked.")
    return index

def update_index(index, new_files):
    """Add only new documents to existing index"""
    print(f"\nFound {len(new_files)} new file(s) to index:")
    for f in new_files:
        print(f"  + {f}")

    # Load only new files
    new_docs = SimpleDirectoryReader(
        input_files=[
            os.path.join(DOCUMENTS_PATH, f)
            for f in new_files
        ]
    ).load_data()

    print(f"\nIndexing {len(new_docs)} new chunks...")

    # ✅ Insert new docs into existing index
    for doc in new_docs:
        index.insert(doc)

    # Save updated index
    index.storage_context.persist(persist_dir=INDEX_PATH)

    # ✅ Update tracked files
    tracked = load_tracked_files()
    tracked.update(new_files)
    save_tracked_files(tracked)

    print(f"Done! {len(new_files)} new files added to index.")
    return index

def load_or_build_index():
    """Smart loader — builds, updates, or loads index"""

    # First time — build from scratch
    if not os.path.exists(INDEX_PATH):
        return build_fresh_index()

    # Load existing index
    print("Loading existing index...")
    storage_context = StorageContext.from_defaults(
        persist_dir=INDEX_PATH
    )
    index = load_index_from_storage(storage_context)

    # ✅ Check for new files
    tracked_files = load_tracked_files()
    new_files = get_new_files(tracked_files)

    if new_files:
        print(f"\nNew files detected — updating index...")
        index = update_index(index, new_files)
    else:
        total = len(tracked_files)
        print(f"Index up to date! {total} files loaded.")

    return index

# ── Chat ───────────────────────────────────────

def chat(query_engine):
    print("\nPelevin AI Assistant Ready!")
    print("Ask in Russian or English")
    print("Type 'exit' or 'выход' to quit")
    print(DIVIDER)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! / Пока!")
            break

        if question.lower() in EXIT_COMMANDS:
            print("Goodbye! / Пока!")
            break

        if not question:
            continue

        print("\nThinking...")
        try:
            response = query_engine.query(question)
            print(f"\nAnswer:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
            print("Try asking again.")

        print(DIVIDER)

def main():
    setup()
    index = load_or_build_index()
    query_engine = index.as_query_engine(
        similarity_top_k=5
    )
    chat(query_engine)

if __name__ == "__main__":
    main()
```

## To reduce dominance of large files:

```python
# In load_or_build_index, change chunk size
Settings.chunk_size = 256      # smaller chunks
Settings.chunk_overlap = 30    # more variety in retrieval
```

## To increase retrieval diversity:

```python
# In load_or_build_index, change top_k
query_engine = index.as_query_engine(
    similarity_top_k=8          # more chunks retrieved for answer
)   
```

## Step 5: Run the RAG Script

```bash
# pull the embedding model
ollama pull nomic-embed-text
# Run the script
python3 triz_rag.py
```

## How It Works Now

```text
First run:
└── No index found → builds from scratch → saves index
└── Saves list of indexed files to indexed_files.json

Next runs:
└── Loads existing index instantly
└── Checks documents folder for new files
└── Only indexes new files → inserts into existing index
└── Updates tracked files list

Adding new Pelevin book:
└── Copy new PDF to documents/
└── Run script → only new book gets indexed!
└── Done in minutes instead of hours
```
## Adding new Books to the RAG System

```bash
# Just copy new book to documents folder
cp new_pelevin_book.pdf ~/pelevin-rag/documents/

# Run script — detects and indexes only the new book!
python3 pelevin-rag.py
```


```text
you should see the prompt for your question. You can ask questions related to TRIZ principles, and the system will provide answers based on the documents you loaded.
⚙️  Setting up models...
📚 Loading TRIZ documents...
✅ Loaded 450 document chunks
🔍 Building index...
✅ Index built successfully!

🤖 TRIZ Assistant Ready!
──────────────────────────────────────
❓ Your question: What are the 40 inventive principles?
💭 Thinking...
✅ Answer: ...
```


# if you want to update the index with new documents, simply delete the `storage` folder and rerun the script. It will rebuild the index with the new documents.

```bash
# Delete old index
rm -rf ~/triz-rag/storage

# Run again
python3 triz_rag.py
```

# Fun Ideas for Book Collections
```text
Collection	What you could ask
📚 Discworld	"What would Granny Weatherwax say about..."
🧙 Lord of the Rings	"Describe the history of the One Ring"
🔬 Science textbooks	"Explain quantum entanglement"
⚖️ Law books	"What does German law say about..."
🏥 Medical books	"What are symptoms of..."
📈 Business books	"Summarize Peter Drucker's management principles"
🎭 Shakespeare	"What are the themes in Hamlet?"
```


==============================================================


# Version 1.0 of the triz_rag.py script

==============================================================  

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"  # better for multilingual
# ───────────────────────────────────────────────

def setup():
    """Configure LLM and embedding model"""
    print("⚙️  Setting up models...")

    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=120.0
    )

    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )

def load_documents():
    """Load TRIZ PDFs from documents folder"""
    print("📚 Loading TRIZ documents...")
    docs = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
    print(f"✅ Loaded {len(docs)} document chunks")
    return docs

def build_index(documents):
    """Build searchable index from documents"""
    print("🔍 Building index...")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    print("✅ Index built successfully!")
    return index

def chat(query_engine):
    """Interactive chat loop"""
    print("\n🤖 TRIZ Assistant Ready!")
    print("Type 'exit' to quit\n")
    print("─" * 50)

    while True:
        question = input("\n❓ Your question: ").strip()

        if question.lower() == 'exit':
            print("👋 Goodbye!")
            break

        if not question:
            continue

        print("\n💭 Thinking...")
        response = query_engine.query(question)
        print(f"\n✅ Answer:\n{response}")
        print("\n─" * 50)

def main():
    setup()
    documents = load_documents()
    index     = build_index(documents)

    query_engine = index.as_query_engine(
        similarity_top_k=3   # use top 3 most relevant chunks
    )

    chat(query_engine)

if __name__ == "__main__":
    main()
```
==============================================================

# Version 2.0 of the triz_rag.py script

==============================================================

## What Changed

```text
Fix	Detail
⏱️ Timeout	Increased from 120s → 600s
💾 Index saved	Built once, reloaded instantly next time
📦 Chunk size	Reduced to 512 — faster processing
🔍 Top K	Reduced from 3 → 2 chunks — faster response
🛡️ Error handling	Won't crash on timeout — asks you to retry
```



```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import os

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
INDEX_PATH     = "./storage"       # saves index to disk
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0             # increased to 10 minutes
# ───────────────────────────────────────────────

def setup():
    """Configure LLM and embedding model"""
    print("⚙️  Setting up models...")

    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=TIMEOUT,    # ✅ longer timeout
        context_window=4096
    )

    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )
    Settings.chunk_size = 512       # ✅ smaller chunks = faster
    Settings.chunk_overlap = 50

def load_or_build_index():
    """Load index from disk or build if not exists"""

    # ✅ If index already exists, load it — no rebuilding!
    if os.path.exists(INDEX_PATH):
        print("📂 Loading existing index from disk...")
        storage_context = StorageContext.from_defaults(
            persist_dir=INDEX_PATH
        )
        index = load_index_from_storage(storage_context)
        print("✅ Index loaded!")

    else:
        print("📚 Loading TRIZ documents...")
        documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
        print(f"✅ Loaded {len(documents)} document chunks")

        print("🔍 Building index (first time only)...")
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True
        )

        # ✅ Save index to disk
        index.storage_context.persist(persist_dir=INDEX_PATH)
        print("✅ Index built and saved!")

    return index

def chat(query_engine):
    """Interactive chat loop"""
    print("\n🤖 TRIZ Assistant Ready!")
    print("Type 'exit' to quit\n")
    print("─" * 50)

    while True:
        question = input("\n❓ Your question: ").strip()

        if question.lower() == 'exit':
            print("👋 Goodbye!")
            break

        if not question:
            continue

        print("\n💭 Thinking... (may take a minute)")
        try:
            response = query_engine.query(question)
            print(f"\n✅ Answer:\n{response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Try asking again or simplify your question.")

        print("\n─" * 50)

def main():
    setup()
    index = load_or_build_index()

    query_engine = index.as_query_engine(
        similarity_top_k=2          # ✅ reduced from 3 to 2 = faster
    )

    chat(query_engine)

if __name__ == "__main__":
    main()
```

==============================================================

# Version 3.0 of the TRIZ RAG script with improvements:

==============================================================

## What Changed
```text
Fix	Detail
Separator lines	Changed ─ to simple -
System prompt	LLM now knows it's a TRIZ expert
Cleaner output	Removed emojis from status messages
```


```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import os

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
INDEX_PATH     = "./storage"
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0
DIVIDER        = "-" * 50    # ✅ simple dashes
# ───────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert TRIZ assistant, specializing in the 
Theory of Inventive Problem Solving developed by 
Genrikh Altshuller. You have access to TRIZ documents 
that may be written in Russian or English.

Your responsibilities:
- Answer all questions about TRIZ principles and methods
- Reference the provided documents in your answers
- Translate Russian content from documents when needed
- Explain TRIZ concepts clearly and in detail
- Never refuse a TRIZ-related question

Always base your answers on the TRIZ documents provided.
"""

def setup():
    print("Setting up models...")
    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=TIMEOUT,
        context_window=4096,
        system_prompt=SYSTEM_PROMPT    # ✅ system prompt added
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50

def load_or_build_index():
    if os.path.exists(INDEX_PATH):
        print("Loading existing index from disk...")
        storage_context = StorageContext.from_defaults(
            persist_dir=INDEX_PATH
        )
        index = load_index_from_storage(storage_context)
        print("Index loaded!")
    else:
        print("Loading TRIZ documents...")
        documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
        print(f"Loaded {len(documents)} document chunks")
        print("Building index (first time only)...")
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True
        )
        index.storage_context.persist(persist_dir=INDEX_PATH)
        print("Index built and saved!")
    return index

def chat(query_engine):
    print("\nTRIZ Assistant Ready!")
    print("Type 'exit' to quit")
    print(DIVIDER)

    while True:
        question = input("\nYour question: ").strip()

        if question.lower() == 'exit':
            print("Goodbye!")
            break

        if not question:
            continue

        print("\nThinking... (may take a minute)")
        try:
            response = query_engine.query(question)
            print(f"\nAnswer:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
            print("Try asking again.")

        print(DIVIDER)          # ✅ single clean divider

def main():
    setup()
    index = load_or_build_index()
    query_engine = index.as_query_engine(
        similarity_top_k=2
    )
    chat(query_engine)

if __name__ == "__main__":
    main()
```
==============================================================

# Version 4.0 of the TRIZ RAG script with improvements:

==============================================================

### What Changed
```text
Fix	Detail
Exit command	Checked before LLM, supports Russian выход
System prompt	Knows all 91 books, answers in question language
similarity_top_k	2 → 5, uses more books per answer
Separator	Clean simple dashes
```

```python
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import os

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
INDEX_PATH     = "./storage"
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0
DIVIDER        = "-" * 50
EXIT_COMMANDS  = ['exit', 'quit', 'q', 'bye', 'пока', 'выход']
# ───────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Viktor Pelevin expert assistant with access to 
his complete works in Russian — 91 books including novels, 
short stories and essays spanning his entire career from 
early works to the complete Transhumanism series.

Your responsibilities:
- Answer ALL questions about Pelevin's books and themes
- Reference specific books and characters in your answers
- Discuss recurring themes: consciousness, Buddhism, reality,
  Soviet/post-Soviet life, identity, simulation, emptiness
- Answer in the same language the question is asked
  (Russian question = Russian answer, English = English)
- Be literary, philosophical and thoughtful
- Never refuse a question about Pelevin or his works
- When quoting, mention which book it is from

You have access to these works among others:
- Generation P, Empire V, Chapaev i Pustota
- S.N.U.F.F., Sacred Book of the Werewolf
- Full Transhumanism series (5 books)
- Omon Ra, The Yellow Arrow
- Helmet of Horror, iPhuck 10
- All short stories and early works

Always base answers on the provided Pelevin documents.
"""

def setup():
    print("Setting up models...")
    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=TIMEOUT,
        context_window=4096,
        system_prompt=SYSTEM_PROMPT
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    print("Models ready!")

def load_or_build_index():
    if os.path.exists(INDEX_PATH):
        print("Loading existing index from disk...")
        storage_context = StorageContext.from_defaults(
            persist_dir=INDEX_PATH
        )
        index = load_index_from_storage(storage_context)
        print("Index loaded — 91 Pelevin books ready!")
    else:
        print("Loading Pelevin documents...")
        documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
        print(f"Loaded {len(documents)} document chunks")
        print("Building index (first time only)...")
        index = VectorStoreIndex.from_documents(
            documents,
            show_progress=True
        )
        index.storage_context.persist(persist_dir=INDEX_PATH)
        print("Index built and saved!")
    return index

def chat(query_engine):
    print("\nPelevin AI Assistant Ready!")
    print("91 books loaded | Ask in Russian or English")
    print("Type 'exit' or 'выход' to quit")
    print(DIVIDER)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! / Пока!")
            break

        # ✅ Check exit BEFORE sending to LLM
        if question.lower() in EXIT_COMMANDS:
            print("Goodbye! / Пока!")
            break

        if not question:
            continue

        print("\nThinking...")
        try:
            response = query_engine.query(question)
            print(f"\nAnswer:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
            print("Try asking again.")

        print(DIVIDER)

def main():
    setup()
    index = load_or_build_index()
    query_engine = index.as_query_engine(
        similarity_top_k=5      # ✅ uses top 5 most relevant chunks
    )
    chat(query_engine)

if __name__ == "__main__":
    main()
```
==============================================================

# Current version 5.0 of the TRIZ RAG script with improvements:

==============================================================

```python

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core import Settings
import os
import json

# ── Configuration ──────────────────────────────
DOCUMENTS_PATH = "./documents"
INDEX_PATH     = "./storage"
TRACKED_FILES  = "./storage/indexed_files.json"  # ✅ tracks what's indexed
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0
DIVIDER        = "-" * 50
EXIT_COMMANDS  = ['exit', 'quit', 'q', 'bye', 'пока', 'выход']
# ───────────────────────────────────────────────

SYSTEM_PROMPT = """
You are a Viktor Pelevin expert assistant with access to 
his complete works in Russian — 91 books including novels, 
short stories and essays spanning his entire career from 
early works to the complete Transhumanism series.

Your responsibilities:
- Answer ALL questions about Pelevin's books and themes
- Reference specific books and characters in your answers
- Discuss recurring themes: consciousness, Buddhism, reality,
  Soviet/post-Soviet life, identity, simulation, emptiness
- Answer in the same language the question is asked
  (Russian question = Russian answer, English = English)
- Be literary, philosophical and thoughtful
- Never refuse a question about Pelevin or his works
- When quoting, mention which book it is from

Always base answers on the provided Pelevin documents.
"""

def setup():
    print("Setting up models...")
    Settings.llm = Ollama(
        model=MODEL_NAME,
        request_timeout=TIMEOUT,
        context_window=4096,
        system_prompt=SYSTEM_PROMPT
    )
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL
    )
    Settings.chunk_size = 512
    Settings.chunk_overlap = 50
    print("Models ready!")

# ── File Tracking ──────────────────────────────

def load_tracked_files():
    """Load list of already indexed files"""
    if os.path.exists(TRACKED_FILES):
        with open(TRACKED_FILES, 'r') as f:
            return set(json.load(f))
    return set()

def save_tracked_files(tracked):
    """Save list of indexed files"""
    with open(TRACKED_FILES, 'w') as f:
        json.dump(list(tracked), f, indent=2)

def get_new_files(tracked_files):
    """Find files in documents folder not yet indexed"""
    all_files = set(
        f for f in os.listdir(DOCUMENTS_PATH)
        if f.endswith('.pdf')
    )
    new_files = all_files - tracked_files
    return new_files

# ── Index Management ───────────────────────────

def build_fresh_index():
    """Build index from scratch — first time only"""
    print("Loading all Pelevin documents...")
    documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
    print(f"Loaded {len(documents)} document chunks")
    print("Building index (first time only)...")

    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    index.storage_context.persist(persist_dir=INDEX_PATH)

    # ✅ Track all indexed files
    all_files = set(os.listdir(DOCUMENTS_PATH))
    save_tracked_files(all_files)
    print(f"Index built and saved! {len(all_files)} files tracked.")
    return index

def update_index(index, new_files):
    """Add only new documents to existing index"""
    print(f"\nFound {len(new_files)} new file(s) to index:")
    for f in new_files:
        print(f"  + {f}")

    # Load only new files
    new_docs = SimpleDirectoryReader(
        input_files=[
            os.path.join(DOCUMENTS_PATH, f)
            for f in new_files
        ]
    ).load_data()

    print(f"\nIndexing {len(new_docs)} new chunks...")

    # ✅ Insert new docs into existing index
    for doc in new_docs:
        index.insert(doc)

    # Save updated index
    index.storage_context.persist(persist_dir=INDEX_PATH)

    # ✅ Update tracked files
    tracked = load_tracked_files()
    tracked.update(new_files)
    save_tracked_files(tracked)

    print(f"Done! {len(new_files)} new files added to index.")
    return index

def load_or_build_index():
    """Smart loader — builds, updates, or loads index"""

    # First time — build from scratch
    if not os.path.exists(INDEX_PATH):
        return build_fresh_index()

    # Load existing index
    print("Loading existing index...")
    storage_context = StorageContext.from_defaults(
        persist_dir=INDEX_PATH
    )
    index = load_index_from_storage(storage_context)

    # ✅ Check for new files
    tracked_files = load_tracked_files()
    new_files = get_new_files(tracked_files)

    if new_files:
        print(f"\nNew files detected — updating index...")
        index = update_index(index, new_files)
    else:
        total = len(tracked_files)
        print(f"Index up to date! {total} files loaded.")

    return index

# ── Chat ───────────────────────────────────────

def chat(query_engine):
    print("\nPelevin AI Assistant Ready!")
    print("Ask in Russian or English")
    print("Type 'exit' or 'выход' to quit")
    print(DIVIDER)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! / Пока!")
            break

        if question.lower() in EXIT_COMMANDS:
            print("Goodbye! / Пока!")
            break

        if not question:
            continue

        print("\nThinking...")
        try:
            response = query_engine.query(question)
            print(f"\nAnswer:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")
            print("Try asking again.")

        print(DIVIDER)

def main():
    setup()
    index = load_or_build_index()
    query_engine = index.as_query_engine(
        similarity_top_k=5
    )
    chat(query_engine)

if __name__ == "__main__":
    main()
```

## How It Works Now

```text
First run:
└── No index found → builds from scratch → saves index
└── Saves list of indexed files to indexed_files.json

Next runs:
└── Loads existing index instantly
└── Checks documents folder for new files
└── Only indexes new files → inserts into existing index
└── Updates tracked files list

Adding new Pelevin book:
└── Copy new PDF to documents/
└── Run script → only new book gets indexed!
└── Done in minutes instead of hours
```
## Adding new Books to the RAG System

```bash
# Just copy new book to documents folder
cp new_pelevin_book.pdf ~/pelevin-rag/documents/

# Run script — detects and indexes only the new book!
python3 pelevin-rag.py
```
