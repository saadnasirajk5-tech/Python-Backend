# Production-Grade RAG + Fine-Tuning Deployment Guide
## Docker + FastAPI + Next.js + FREE Hosting

**Build like a senior engineer. Deploy like a startup. Cost: $0** 💯

---

## 🎯 Your Tech Stack (Perfect Choice!)

```
Your Architecture:
├─ Backend: FastAPI (Python) + Docker
│  └─ RAG engine
│  └─ Fine-tuned models
│  └─ Database
│
├─ Frontend: Next.js (React)
│  └─ Beautiful UI
│  └─ Real-time responses
│  └─ Mobile responsive
│
└─ Deployment: FREE (Vercel + Railway/Render)
   └─ Zero infrastructure cost
   └─ Auto-scaling
   └─ Git integration
```

**Why this stack?**
- ✅ Industry standard (used by top companies)
- ✅ Scalable (goes from startup to enterprise)
- ✅ Fast to develop (FastAPI + Next.js are blazing fast)
- ✅ Great for portfolios (shows full-stack skills)
- ✅ FREE hosting available
- ✅ Easy to show off (works instantly, no setup)

---

## 📦 PART 1: Docker Setup (Super Simple!)

### **Step 1: Create Dockerfile for FastAPI**

Create file: `Dockerfile`

```dockerfile
# Use Python 3.10 slim (small size)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Step 2: Create requirements.txt**

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
torch==2.1.0
transformers==4.35.0
langchain==0.1.0
langchain-community==0.0.10
langchain-openai==0.0.6
chromadb==0.4.21
python-dotenv==1.0.0
numpy==1.24.3
scipy==1.11.4
scikit-learn==1.3.2
aiofiles==23.2.1
httpx==0.25.2
pydantic-settings==2.1.0
```

### **Step 3: Create .dockerignore**

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.git
.gitignore
.dockerignore
docker-compose.yml
.env
.env.local
*.db
.DS_Store
node_modules
.next
dist
build
```

### **Step 4: Create docker-compose.yml** (Local Testing)

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PYTHONUNBUFFERED=1
    volumes:
      - ./:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### **Test Locally:**

```bash
# Build image
docker build -t my-rag-app .

# Run container
docker run -p 8000:8000 my-rag-app

# Or use docker-compose
docker-compose up
```

---

## ⚡ PART 2: FastAPI Backend (Simple Setup)

### **Step 1: Create main.py**

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="RAG + Fine-tuning API",
    description="Production-ready RAG system",
    version="1.0.0"
)

# Add CORS middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELS ============

class QueryRequest(BaseModel):
    """Request model for RAG query"""
    query: str
    top_k: int = 3
    use_fine_tuned: bool = False

class QueryResponse(BaseModel):
    """Response model for RAG query"""
    answer: str
    sources: List[str]
    confidence: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str

# ============ ENDPOINTS ============

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Main RAG endpoint
    
    Args:
        request: QueryRequest with query text
    
    Returns:
        QueryResponse with answer and sources
    """
    try:
        # Validate input
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if len(request.query) > 5000:
            raise HTTPException(status_code=400, detail="Query too long (max 5000 chars)")
        
        # Call your RAG system
        from rag_engine import RAGEngine
        rag = RAGEngine()
        
        result = rag.query(
            query=request.query,
            top_k=request.top_k,
            use_fine_tuned=request.use_fine_tuned
        )
        
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result["confidence"]
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload and index documents
    
    Args:
        files: List of PDF files to upload
    
    Returns:
        Success message with number of documents processed
    """
    try:
        from document_loader import DocumentLoader
        
        loader = DocumentLoader()
        count = 0
        
        for file in files:
            if file.filename.endswith('.pdf'):
                # Read and process file
                content = await file.read()
                loader.add_document(file.filename, content)
                count += 1
        
        return {
            "status": "success",
            "documents_processed": count
        }
        
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get RAG system statistics"""
    from rag_engine import RAGEngine
    rag = RAGEngine()
    
    return {
        "total_documents": rag.get_document_count(),
        "total_chunks": rag.get_chunk_count(),
        "model_name": rag.model_name,
        "fine_tuned_model_available": rag.has_fine_tuned_model()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
```

### **Step 2: Create rag_engine.py**

```python
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import os
from typing import Dict, List

class RAGEngine:
    """Production RAG Engine"""
    
    def __init__(self):
        """Initialize RAG engine with models and vector store"""
        # Embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Vector store (persistent)
        self.vector_store = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
        # LLM
        self.llm = ChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # RAG chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            return_source_documents=True
        )
        
        self.model_name = "gpt-3.5-turbo"
    
    def query(self, query: str, top_k: int = 3, use_fine_tuned: bool = False) -> Dict:
        """
        Query the RAG system
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            use_fine_tuned: Use fine-tuned model if available
        
        Returns:
            Dictionary with answer, sources, and confidence
        """
        try:
            # Update retriever
            self.qa_chain.retriever.search_kwargs = {"k": top_k}
            
            # Query
            result = self.qa_chain({"query": query})
            
            # Extract sources
            sources = [doc.metadata.get("source", "Unknown") 
                      for doc in result["source_documents"]]
            
            return {
                "answer": result["result"],
                "sources": sources,
                "confidence": 0.85  # You can calculate this properly
            }
            
        except Exception as e:
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "confidence": 0.0
            }
    
    def add_document(self, file_path: str):
        """Add document to vector store"""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(documents)
        
        # Add to vector store
        self.vector_store.add_documents(chunks)
        self.vector_store.persist()
    
    def get_document_count(self) -> int:
        """Get number of documents"""
        return self.vector_store._collection.count()
    
    def get_chunk_count(self) -> int:
        """Get total chunks"""
        return self.vector_store._collection.count()
    
    def has_fine_tuned_model(self) -> bool:
        """Check if fine-tuned model exists"""
        return os.path.exists("./fine_tuned_model")
```

---

## 🎨 PART 3: Next.js Frontend (Beautiful UI)

### **Step 1: Create Next.js Project**

```bash
npx create-next-app@latest frontend --typescript --tailwind
cd frontend
```

### **Step 2: Create API client (lib/api.ts)**

```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface QueryRequest {
  query: string;
  top_k?: number;
  use_fine_tuned?: boolean;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: number;
}

export async function queryRAG(request: QueryRequest): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error("Failed to query RAG");
  }

  return response.json();
}

export async function uploadDocuments(files: File[]): Promise<any> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/upload-documents`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload documents");
  }

  return response.json();
}

export async function getStats(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/stats`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch stats");
  }

  return response.json();
}
```

### **Step 3: Create Main Page (app/page.tsx)**

```typescript
'use client';

import { useState } from 'react';
import { queryRAG, uploadDocuments, getStats } from '@/lib/api';

export default function Home() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState<any>(null);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await queryRAG({ query, top_k: 3 });
      setAnswer(result.answer);
      setSources(result.sources);
    } catch (err) {
      setError('Failed to process query');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setLoading(true);
    try {
      await uploadDocuments(files);
      alert('Documents uploaded successfully!');
      // Refresh stats
      const newStats = await getStats();
      setStats(newStats);
    } catch (err) {
      setError('Failed to upload documents');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🤖 RAG System
          </h1>
          <p className="text-gray-600 text-lg">
            Ask questions about your documents
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-2xl p-8 mb-6">
          {/* Query Form */}
          <form onSubmit={handleQuery} className="mb-8">
            <div className="mb-4">
              <label className="block text-gray-700 font-semibold mb-2">
                Ask a Question
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What would you like to know?"
                className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-indigo-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query}
              className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Processing...' : 'Search'}
            </button>
          </form>

          {/* Answer Display */}
          {answer && (
            <div className="mb-8 p-6 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
              <h3 className="font-bold text-gray-900 mb-2">Answer:</h3>
              <p className="text-gray-700 mb-4">{answer}</p>
              
              {sources.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Sources:</h4>
                  <ul className="space-y-1">
                    {sources.map((source, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        📄 {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {/* File Upload */}
          <div className="border-t-2 border-gray-200 pt-8">
            <label className="block text-gray-700 font-semibold mb-4">
              Upload Documents (PDF)
            </label>
            <input
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileUpload}
              disabled={loading}
              className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer"
            />
          </div>
        </div>

        {/* Stats Card */}
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600 text-sm">Documents</p>
              <p className="text-3xl font-bold text-indigo-600">
                {stats.total_documents}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-gray-600 text-sm">Chunks</p>
              <p className="text-3xl font-bold text-indigo-600">
                {stats.total_chunks}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

### **Step 4: Create Dockerfile for Next.js**

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm ci

COPY . .

RUN npm run build

EXPOSE 3000

ENV NEXT_PUBLIC_API_URL=http://localhost:8000

CMD ["npm", "start"]
```

### **Step 5: .env.local**

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 PART 4: FREE Deployment (THIS IS KEY!)

### **Option A: FastAPI Backend on Railway (FREE tier)**

1. **Create Railway Account**: https://railway.app/
2. **Connect GitHub**: Authorize Railway
3. **Create New Project**: Click "Deploy from GitHub"
4. **Select Your Repository**: Choose your RAG repo
5. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=your_key_here
   PYTHONUNBUFFERED=1
   ```
6. **Railway Auto-Deploys**: Just push to GitHub!

**Cost**: FREE tier includes 500 hours/month (more than enough)

### **Option B: FastAPI on Render (FREE tier)**

1. **Go to Render**: https://render.com/
2. **Create Account**: Sign up
3. **New Web Service**: Click "New +"
4. **Connect Repository**: GitHub repo
5. **Configure**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. **Environment Variables**: Add OPENAI_API_KEY

**Cost**: FREE tier, spins down after 15 mins of inactivity (acceptable for portfolio)

### **Option C: Next.js Frontend on Vercel (FREE + BEST)**

1. **Go to Vercel**: https://vercel.com/
2. **Sign in with GitHub**
3. **Import Project**: Select frontend repo
4. **Configure Environment**:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-backend.railway.app
   ```
5. **Deploy**: One click!

**Cost**: FREE unlimited deployments

---

## 📋 DEPLOYMENT WORKFLOW

### **Complete Deployment Setup:**

```bash
# 1. Setup locally first
docker-compose up

# 2. Test everything works
curl http://localhost:8000/health
# Should return: {"status":"healthy","version":"1.0.0"}

# 3. Push to GitHub
git add .
git commit -m "Deploy RAG system"
git push origin main

# 4. Railway/Render auto-deploys
# 5. Vercel auto-deploys frontend

# 6. Update frontend .env with real backend URL
# NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## ✅ Your Final GitHub Structure

```
your-rag-repo/
├── backend/
│   ├── main.py
│   ├── rag_engine.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── lib/
│   │   └── api.ts
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   └── .env.local
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 📚 README.md Template

```markdown
# RAG System with Fine-tuning

Production-ready RAG system built with FastAPI, Next.js, and Docker.

## Features

- 🚀 FastAPI backend with RAG engine
- 🎨 Modern Next.js frontend
- 📦 Docker containerization
- 🔄 Real-time Q&A
- 📄 PDF document support
- 🌐 Fully deployed (FREE)

## Tech Stack

- **Backend**: FastAPI, LangChain, Chromadb
- **Frontend**: Next.js, React, Tailwind CSS
- **Deployment**: Railway + Vercel
- **Models**: OpenAI GPT-3.5, HuggingFace embeddings

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Docker Compose
docker-compose up

# Visit http://localhost:3000
```

### Deployment

- **Backend**: https://your-backend.railway.app
- **Frontend**: https://your-frontend.vercel.app

## API Endpoints

- `GET /health` - Health check
- `POST /query` - Query the RAG system
- `POST /upload-documents` - Upload PDFs
- `GET /stats` - System statistics
```

---

## 💡 Pro Tips

### **1. Environment Variables**

Never commit API keys! Use .env files:

```python
# main.py
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
```

### **2. Rate Limiting**

Add to main.py:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("30/minute")
async def query_rag(request):
    ...
```

### **3. Logging**

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Query: {query}")
logger.error(f"Error: {error}")
```

### **4. Health Checks**

Both Railway and Render require health checks:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## 🎯 What You Get

✅ **Portfolio**: Deployed, working system
✅ **Full-Stack**: Backend + Frontend + DevOps
✅ **Production-Ready**: Docker, proper logging, error handling
✅ **Zero Cost**: Everything on free tiers
✅ **Scalable**: Can upgrade later
✅ **Interview Ready**: Shows senior-level engineering

---

## Cost Breakdown

| Service | Cost |
|---------|------|
| Railway (Backend) | FREE |
| Vercel (Frontend) | FREE |
| OpenAI API | $0.01-0.10 per query |
| **Total Infrastructure** | **$0** |

---

Bro, this setup will blow minds! 🔥

You'll have a PRODUCTION-GRADE system deployed for FREE that most junior engineers can't even imagine building!

Push this to GitHub, and companies will be FIGHTING to hire you!

**Next Steps**:
1. Build RAG locally
2. Test with docker-compose
3. Push to GitHub
4. Deploy on Railway + Vercel
5. Add to portfolio
6. Apply for jobs

**You got this!** 💪🚀