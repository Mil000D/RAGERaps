# RAGERaps

RAGERaps is an AI rap battle application using Python with uv for backend and Angular for frontend, featuring RAG-based style interpretation and web search for biographical information.

## Setup

### Backend

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a `.env` file based on the example:
```bash
cp .env.example .env
```

3. Update the `.env` file with your API keys and configuration.

### Qdrant Configuration

RAGERaps uses Qdrant as a vector database for storing and retrieving rap styles. You can use either a local Qdrant instance or a cloud-hosted Qdrant cluster.

#### Local Qdrant

To use a local Qdrant instance, set the following in your `.env` file:
```
QDRANT_URL=http://localhost:6333
# No API key needed for local instance
```

#### Cloud Qdrant

To use a cloud-hosted Qdrant cluster, set the following in your `.env` file:
```
QDRANT_URL=https://your-qdrant-cluster-url.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

### Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
ng serve
```

3. Open your browser and navigate to `http://localhost:4200`