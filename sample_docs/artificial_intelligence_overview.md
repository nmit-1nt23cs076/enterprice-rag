# Introduction to Retrieval-Augmented Generation (RAG)

## What is RAG?
Retrieval-Augmented Generation (RAG) is an architectural pattern that optimizes the output of large language models (LLMs) by referencing an authoritative knowledge base outside of its training data sources before generating a response.

## Core Components of a RAG Pipeline
1. **Document Ingestion & Chunking**: Documents are split into semantic chunks (e.g. 200–800 tokens) with sliding overlap to maintain semantic continuity.
2. **Vector Indexing**: Text chunks are converted into dense vector embeddings using an embedding model and stored in a vector index (e.g., ChromaDB, FAISS, Pinecone, or BM25 hybrid stores).
3. **Retrieval**: When a user poses a query, the system identifies the top-k most semantically similar chunks via cosine similarity or BM25 relevance scoring.
4. **Augmentation**: The retrieved passages are injected into the prompt alongside instructions and the user question.
5. **Generation**: The LLM synthesizes an accurate, grounded answer using the provided context, citing specific sources and preventing hallucinations.

## Advantages of RAG
- **Reduces Hallucinations**: Grounds responses in real-time or private proprietary data.
- **Cost Effective**: Avoids expensive model fine-tuning for rapidly changing knowledge bases.
- **Traceability**: Provides precise citations (page numbers, filenames, and chunk excerpts) so users can verify statements.
