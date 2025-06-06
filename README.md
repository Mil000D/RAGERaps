# 🎤 RAGERaps

> 🔥 **AI Rap Battle Arena** - Where artificial minds drop bars and spit fire! 🔥

RAGERaps is an AI-powered rap battle application that combines cutting-edge RAG technology with parallel agent execution to create epic lyrical showdowns. Built with FastAPI backend and Angular frontend.

## 🚀 Quick Start

### 📋 Prerequisites
- 🐍 Python 3.13+ with [uv](https://docs.astral.sh/uv/) package manager
- 📦 Node.js 18+ and npm
- 🗄️ Qdrant vector database (local or cloud)

### ⚙️ Backend Setup

1. 📁 Navigate to the backend directory:
```bash
cd backend
```

2. 📥 Install dependencies:
```bash
uv sync
```

3. 🔑 Create a `.env` file with required API keys:
```bash
cp .env.example .env
```

4. ✏️ Update the `.env` file with your configuration:
```env
OPENAI_API_KEY=your-openai-api-key
TAVILY_API_KEY=your-tavily-api-key
QDRANT_URL=http://localhost:6333  # or your cloud URL
QDRANT_API_KEY=your-qdrant-api-key  # only for cloud
LANGSMITH_API_KEY=your-langsmith-key  # optional
```

### 🎨 Frontend Setup

1. 📁 Navigate to the frontend directory:
```bash
cd frontend
```

2. 📥 Install dependencies:
```bash
npm install
```

### 🗄️ Qdrant Configuration

RAGERaps uses Qdrant as a vector database for storing and retrieving rap styles. Choose your setup:

#### 🏠 Local Qdrant
```env
QDRANT_URL=http://localhost:6333
# No API key needed for local instance
```

#### ☁️ Cloud Qdrant
```env
QDRANT_URL=https://your-qdrant-cluster-url.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

## 🎵 Running the Application

### 🚀 Start Backend
```bash
cd backend
uvicorn main:app --reload
```
> ⚠️ **Note**: You may see SyntaxWarnings from the Qdrant library - these are harmless and can be ignored.

### 🎨 Start Frontend
```bash
cd frontend
ng serve
```

### 🌐 Access the Battle Arena
- 🎤 **Frontend**: `http://localhost:4200`
- 🔧 **Backend API**: `http://localhost:8000`

---

## 🎯 Features

- 🤖 **AI Rappers**: Multiple AI agents with distinct styles
- ⚡ **Parallel Battles**: Simultaneous verse generation
- 🔍 **RAG-Powered**: Vector search for authentic style matching
- 🏆 **AI Judging**: Automated battle scoring
- 🌐 **Web Integration**: Real-time artist data retrieval

---

*Ready to witness the future of rap battles? Let the AI cypher begin! 🎤🔥*