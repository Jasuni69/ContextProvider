import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import uuid
from ..core.config import settings


class VectorService:
    def __init__(self):
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_document_chunks(self, document_id: int, chunks: List[str], metadata: Dict[str, Any] = None) -> List[str]:
        """Add document chunks to the vector store"""
        chunk_ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"doc_{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}"
            chunk_ids.append(chunk_id)
            
            # Generate embedding
            embedding = self.embedding_model.encode(chunk).tolist()
            embeddings.append(embedding)
            
            # Prepare metadata
            chunk_metadata = {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_length": len(chunk),
                **(metadata or {})
            }
            metadatas.append(chunk_metadata)
            documents.append(chunk)
        
        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        
        return chunk_ids
    
    def search_similar_chunks(self, query: str, n_results: int = 5, document_ids: List[int] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks based on query"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Prepare where clause for filtering by document IDs
        where_clause = None
        if document_ids:
            where_clause = {"document_id": {"$in": document_ids}}
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "similarity": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
        
        return formatted_results
    
    def delete_document_chunks(self, document_id: int):
        """Delete all chunks for a specific document"""
        # Get all chunk IDs for the document
        results = self.collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )
        
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection_name": self.collection.name
        } 