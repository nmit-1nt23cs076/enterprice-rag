import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from app.rag_engine import RAGEngine
from app.config import UPLOAD_DIR, BASE_DIR, TOP_K_RESULTS

app = FastAPI(
    title="RAG Document Q&A API",
    description="Production-ready Retrieval-Augmented Generation API for Documents (PDF, TXT, MD)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_engine = RAGEngine()

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = TOP_K_RESULTS

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "indexed_documents": len(rag_engine.indexed_files),
        "total_chunks": len(rag_engine.vector_store.chunks)
    }

@app.get("/api/documents")
def list_documents():
    return {
        "documents": list(rag_engine.indexed_files.values()),
        "total_documents": len(rag_engine.indexed_files),
        "total_chunks": len(rag_engine.vector_store.chunks)
    }

@app.post("/api/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    results = []
    for file in files:
        doc_id = str(uuid.uuid4())[:8]
        safe_filename = Path(file.filename).name
        saved_path = UPLOAD_DIR / f"{doc_id}_{safe_filename}"

        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        num_chunks = rag_engine.index_document(doc_id, safe_filename, saved_path)
        results.append({
            "doc_id": doc_id,
            "filename": safe_filename,
            "chunks_created": num_chunks
        })

    return {
        "message": f"Successfully indexed {len(files)} document(s).",
        "documents": results,
        "total_chunks": len(rag_engine.vector_store.chunks)
    }

@app.post("/api/query")
def query_rag(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    response = rag_engine.query(req.query, top_k=req.top_k or 4)
    return response

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    success = rag_engine.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": "Document successfully deleted from vector index."}

# Mount frontend static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
