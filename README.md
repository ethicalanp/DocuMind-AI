# DocuMind AI

**Transform your documents into intelligent conversations.**

DocuMind AI is an AI-powered document intelligence platform that lets you upload business documents and ask natural language questions about them. Using retrieval-augmented generation (RAG) and advanced language models, it provides accurate, grounded answers backed by your source documents.

## Features

- **📄 Multi-Format Document Support** — Upload PDFs, DOCX, and TXT files
- **🔍 Semantic Search** — Find relevant content across your entire document library
- **💬 Intelligent Conversations** — Ask questions in plain language and get grounded answers
- **📌 Source Citations** — Every answer includes references to the documents it's based on
- **🗂️ Conversation History** — Organize and revisit multiple conversations with your documents
- **🔐 User Authentication** — Secure login with JWT-based access control
- **📊 Document Management** — Upload, download, and delete documents with processing status tracking
- **⚡ Real-Time Indexing** — Documents are automatically chunked and indexed for fast retrieval

## Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Store**: [ChromaDB](https://www.trychroma.com/) — Embedding storage and retrieval
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **LLM**: [Groq API](https://console.groq.com) with OpenAI-compatible interface
- **Authentication**: JWT tokens with bcrypt password hashing
- **Document Processing**: PyPDF, python-docx, and text extraction

### Frontend
- **Framework**: [React 19](https://react.dev/) with Vite
- **HTTP Client**: Axios
- **Routing**: React Router
- **Styling**: Modern CSS with responsive design
- **Build Tool**: Vite with optimized production builds

### Prerequisites

- Python 3.8+
- Node.js 18+
- Groq API key ([Get one here](https://console.groq.com))

### Installation

#### 1. Clone and Setup Backend

```bash
cd DocuMind-AI/backend
python -m venv ../venv
source ../venv/bin/activate  # On Windows: ../venv\Scripts\activate
pip install -r ../requirements.txt
```

#### 2. Configure Environment

Create a `.env` file in the project root:

```env
# Authentication
SECRET_KEY=your-secure-random-key-at-least-32-characters-long

# LLM Configuration
LLM_API_KEY=your-groq-api-key
LLM_MODEL=mixtral-8x7b-32768
LLM_BASE_URL=https://api.groq.com/openai/v1
```

#### 3. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

#### 4. Setup and Run Frontend

```bash
cd frontend
npm install
npm run dev
```

## License

This project is provided as-is for educational and commercial use.

## Support

For issues, questions, or feedback, please refer to the project documentation or check the GitHub repository.
