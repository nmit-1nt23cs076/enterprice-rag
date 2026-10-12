# ⚡ DocuRAG: Document Q&A Retrieval-Augmented Generation System

A production-ready **Retrieval-Augmented Generation (RAG)** application designed for high-precision document question-answering. Built with a high-performance **FastAPI** backend, hybrid vector/BM25 retrieval engine, and an interactive **dark-mode web dashboard**.

---

## 🌟 Key Features

- **Multi-Format Ingestion**: Upload and index `.pdf`, `.txt`, `.md`, and `.csv` files.
- **Recursive Text Chunking**: Semantic sliding-window chunking with configurable overlap.
- **Hybrid Retrieval Engine**: Low-latency top-$k$ similarity matching with BM25 / dense scoring.
- **Source Verification & Citations**: Every generated answer includes clickable source pills, chunk indices, and relevance scores.
- **Interactive UI**: Drag-and-drop file upload, live chunk count counters, and real-time chat stream.
- **Zero-Dependency Startup**: Operates seamlessly out-of-the-box without requiring mandatory cloud API keys; supports optional OpenAI/Gemini/Ollama plug-ins.

---

## 🏗️ Architecture

```
[ Documents (PDF, MD, TXT) ]
             │
             ▼
[ Document Parser & Chunking ]
             │
             ▼
[ Vector & Inverted Index Store ] ◄───► [ Query: User Question ]
             │                                   │
             ▼                                   ▼
      [ Top-K Chunks ]                    [ Retrieval ]
             │                                   │
             └───────────────┬───────────────────┘
                             ▼
                 [ Augmented Context ]
                             │
                             ▼
             [ Answer Synthesis & Citations ]
                             │
                             ▼
                 [ Interactive Web UI ]
```

---

## 🚀 Quick Start

### 1. Clone & Navigate
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd rag-document-qa
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
python run.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to start querying documents.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/upload` | Upload multiple files (`multipart/form-data`) and index them |
| `POST` | `/api/query` | Submit a user query and retrieve grounded answer + sources |
| `GET` | `/api/documents` | List all indexed files, chunk counts, and timestamps |
| `DELETE` | `/api/documents/{doc_id}` | Remove a document from the vector store |
| `GET` | `/api/health` | Health check endpoint |

---

## 🛠️ Project Structure

```
rag-document-qa/
├── app/
│   ├── config.py         # App configuration & environment settings
│   ├── main.py           # FastAPI server and REST endpoints
│   └── rag_engine.py     # Parser, chunker, vector store, and generator
├── sample_docs/
│   └── artificial_intelligence_overview.md
├── static/
│   ├── app.js            # Frontend chat & upload logic
│   ├── index.html        # Interactive web dashboard
│   └── style.css         # Modern glassmorphic styles
├── requirements.txt      # Python dependencies
├── run.py                # Server launcher script
└── README.md             # Documentation
```

---

## 📄 License
MIT License. Free for academic, personal, and commercial use.
