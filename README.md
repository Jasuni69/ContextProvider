# AI-Powered Document Chatbot

A fullstack AI-powered chatbot that lets users upload files (CSV, PDF, TXT), then ask natural language questions about the content. The app combines vector-based search with a large language model to provide intelligent, context-aware answers based on the uploaded documents.

## 🚀 Features

- 📁 Upload CSV, TXT, or PDF files
- 🧠 Embed and store document chunks in ChromaDB
- 🔍 Ask natural language questions across all uploaded files
- 📊 Support for both structured and unstructured data
- 💬 Responsive chatbot interface with chat history
- 🛡️ Secure, modular FastAPI backend with SQLAlchemy for tracking user sessions, uploads, and messages

## ⚙️ Tech Stack

**Frontend:** React + Vite + TailwindCSS  
**Backend:** FastAPI + SQLAlchemy + PostgreSQL  
**Vector Store:** ChromaDB  
**AI/NLP:** SentenceTransformers + OpenAI GPT-4  
**File Handling:** pandas, PyMuPDF  

## 🛠️ Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- OpenAI API Key (optional, for GPT-4 integration)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Database Setup

1. Create a PostgreSQL database:
   ```sql
   CREATE DATABASE contextprovider;
   ```

2. Update the database URL in your `.env` file.

## 🚀 Usage

1. Open your browser and navigate to `http://localhost:5173`
2. Upload your documents (CSV, PDF, or TXT files)
3. Start asking questions about your documents!

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── alembic/            # Database migrations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Utility functions
│   └── package.json        # Node dependencies
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
DATABASE_URL=postgresql://username:password@localhost/contextprovider
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License. 