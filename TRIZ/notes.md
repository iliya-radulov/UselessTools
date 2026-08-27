# Local RAG Projects — Setup & Reference Notes

Two separate RAG projects built on M4 Mac using Ollama + LlamaIndex:
- **TRIZ RAG** — Altshuller's TRIZ methodology (Russian technical literature)
- **Pelevin RAG** — Viktor Pelevin's complete works (Russian fiction)

Both share the same architecture and can be adapted for any document collection.

---

## Hardware

| Machine | Use |
|---------|-----|
| M4 Mac | Development, prototyping, running both RAG systems |
| Ryzen 9900X + RTX 5060 16GB (incoming) | Fine-tuning, larger models |

### Future plan (RTX 5060)
```
└── Fine-tune Llama 8B on TRIZ dataset
└── Run RAG with Mistral 7B
└── Use quantized models for larger LLMs
```

---

## Step 1 — Install Ollama & Python Packages

```bash
# Install Ollama
brew install ollama

# Pull the LLM model
ollama pull llama3.1

# Pull the embedding model (required!)
ollama pull nomic-embed-text

# Install Python packages
pip3 install llama-index llama-index-llms-ollama llama-index-embeddings-ollama
```

---

## Step 2 — Test Ollama

```bash
# Start Ollama in background
ollama serve

# Open a new terminal tab (CMD+T) and test interactively
ollama run llama3.1

# Or pipe a question directly
echo "What are the 40 TRIZ principles?" | ollama run llama3.1
```

---

## Step 3 — Create Project Folders

```bash
# TRIZ project
mkdir ~/triz-rag
cd ~/triz-rag
mkdir documents

# Pelevin project
mkdir ~/pelevin-rag
cd ~/pelevin-rag
mkdir documents

# Copy your PDF documents into the respective documents/ folder
```

---

## Step 3b — Convert Documents to PDF

### EPUB / FB2 (Calibre)
```bash
brew install calibre

# Single EPUB
ebook-convert yourbook.epub yourbook.pdf

# Single FB2
ebook-convert yourbook.fb2 yourbook.pdf

# Batch convert all EPUBs in a folder
for f in ~/books/*.epub; do
    ebook-convert "$f" "${f%.epub}.pdf"
    echo "Converted: $f"
done

# Batch convert all FB2s in a folder
for f in ~/books/*.fb2; do
    ebook-convert "$f" "${f%.fb2}.pdf"
    echo "Converted: $f"
done
```

### DJVU
```bash
brew install djvulibre

# Single file
ddjvu -format=pdf yourbook.djvu yourbook.pdf

# Batch
for f in ~/books/*.djvu; do
    ddjvu -format=pdf "$f" "${f%.djvu}.pdf"
    echo "Converted: $f"
done
```

### DOC / DOCX
```bash
brew install libreoffice
libreoffice --convert-to pdf yourfile.doc
```

### Audiobooks → Text (Whisper)
```bash
# Install tools
pip3 install openai-whisper
brew install ffmpeg

# Single audiobook
whisper audiobook.mp3 --language Russian --output_format txt

# Batch processing
for f in ~/audiobooks/*.mp3; do
    whisper "$f" --language Russian --output_format txt
    echo "Done: $f"
done
```

---

## The RAG Script — Final Version

> Same script used for both projects — only the `SYSTEM_PROMPT`,
> `DOCUMENTS_PATH` and project name change between them.

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
TRACKED_FILES  = "./storage/indexed_files.json"
MODEL_NAME     = "llama3.1"
EMBED_MODEL    = "nomic-embed-text"
TIMEOUT        = 600.0
DIVIDER        = "-" * 50
EXIT_COMMANDS  = ['exit', 'quit', 'q', 'bye', 'пока', 'выход']
# ───────────────────────────────────────────────

# ── Swap this prompt per project ───────────────
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
- You have access to 91 complete Pelevin works.
  Never state how many documents you can see —
  you have access to his complete bibliography.

Always base answers on the provided Pelevin documents.
"""

# ── TRIZ version of the prompt (swap when needed) ──
# SYSTEM_PROMPT = """
# You are an expert TRIZ assistant, specializing in the
# Theory of Inventive Problem Solving developed by
# Genrikh Altshuller. You have access to TRIZ documents
# that may be written in Russian or English.
#
# Your responsibilities:
# - Answer all questions about TRIZ principles and methods
# - Reference the provided documents in your answers
# - Translate Russian content from documents when needed
# - Explain TRIZ concepts clearly and in detail
# - Never refuse a TRIZ-related question
# - Never state how many documents you can see
#
# Always base your answers on the TRIZ documents provided.
# """
# ───────────────────────────────────────────────

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
    Settings.chunk_size = 256       # smaller = more diverse retrieval
    Settings.chunk_overlap = 30
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
    """Find PDF files in documents folder not yet indexed"""
    all_files = set(
        f for f in os.listdir(DOCUMENTS_PATH)
        if f.endswith('.pdf')
    )
    new_files = all_files - tracked_files
    return new_files

# ── Index Management ───────────────────────────

def build_fresh_index():
    """Build index from scratch — first time only"""
    print("Loading documents...")
    documents = SimpleDirectoryReader(DOCUMENTS_PATH).load_data()
    print(f"Loaded {len(documents)} document chunks")
    print("Building index (first time only)...")

    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True
    )
    index.storage_context.persist(persist_dir=INDEX_PATH)

    all_files = set(os.listdir(DOCUMENTS_PATH))
    save_tracked_files(all_files)
    print(f"Index built and saved! {len(all_files)} files tracked.")
    return index

def update_index(index, new_files):
    """Add only new documents to existing index"""
    print(f"\nFound {len(new_files)} new file(s) to index:")
    for f in new_files:
        print(f"  + {f}")

    new_docs = SimpleDirectoryReader(
        input_files=[
            os.path.join(DOCUMENTS_PATH, f)
            for f in new_files
        ]
    ).load_data()

    print(f"\nIndexing {len(new_docs)} new chunks...")

    for doc in new_docs:
        index.insert(doc)

    index.storage_context.persist(persist_dir=INDEX_PATH)

    tracked = load_tracked_files()
    tracked.update(new_files)
    save_tracked_files(tracked)

    print(f"Done! {len(new_files)} new files added to index.")
    return index

def load_or_build_index():
    """Smart loader — builds fresh, updates, or loads existing index"""

    if not os.path.exists(INDEX_PATH):
        return build_fresh_index()

    print("Loading existing index...")
    storage_context = StorageContext.from_defaults(
        persist_dir=INDEX_PATH
    )
    index = load_index_from_storage(storage_context)

    tracked_files = load_tracked_files()
    new_files = get_new_files(tracked_files)

    if new_files:
        print("New files detected — updating index...")
        index = update_index(index, new_files)
    else:
        print(f"Index up to date! {len(tracked_files)} files loaded.")

    return index

# ── Chat ───────────────────────────────────────

def chat(query_engine):
    print("\nAssistant Ready!")
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
        similarity_top_k=8          # top 8 chunks = better coverage
    )
    chat(query_engine)

if __name__ == "__main__":
    main()
```

---

## How Incremental Indexing Works

```
First run:
└── No index found → builds from scratch → saves index
└── Saves list of indexed files to indexed_files.json

Next runs:
└── Loads existing index instantly (~5 seconds)
└── Checks documents folder for new files
└── Only indexes new files → inserts into existing index
└── Updates tracked files list

Adding a new book:
└── Copy new PDF to documents/
└── Run script → detects and indexes only the new file
└── Done in minutes instead of hours
```

### Rebuild index from scratch

```bash
# Only needed if you want a completely fresh start
rm -rf ~/triz-rag/storage
python3 triz_rag.py
```

---

## Adding New Books

```bash
# Copy new book to documents folder
cp new_book.pdf ~/pelevin-rag/documents/

# Run — detects and indexes only the new book
python3 pelevin-rag.py
```

---

## Expected Indexing Times

| Scenario | Time |
|----------|------|
| First build (10 books) | ~30-60 min |
| First build (91 books) | ~2-4 hours |
| Load existing index | ~5 seconds |
| Add 1 new book | ~2-3 minutes |
| Add 5 new books | ~10-15 minutes |

---

## Key Settings Reference

| Setting | Value | Why |
|---------|-------|-----|
| `chunk_size` | 256 | Smaller = more diverse retrieval |
| `chunk_overlap` | 30 | Avoids cutting sentences mid-thought |
| `similarity_top_k` | 8 | More chunks = broader book coverage |
| `request_timeout` | 600.0 | 10 min — needed for large documents |
| `context_window` | 4096 | llama3.1 default |

---

## Project File Structure

```
~/triz-rag/               ~/pelevin-rag/
├── documents/            ├── documents/
│   └── *.pdf             │   └── *.pdf
├── storage/              ├── storage/
│   ├── *.json            │   ├── *.json
│   └── indexed_files.json│   └── indexed_files.json
└── triz_rag.py           └── pelevin-rag.py
```

---

## Extending to Other Collections

The same script works for any document collection — just change:
1. `DOCUMENTS_PATH` to point to your documents folder
2. `SYSTEM_PROMPT` to describe the new domain
3. Rename the script

Ideas: Discworld, materials science papers, legal documents,
medical textbooks, any research domain.
