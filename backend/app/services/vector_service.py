import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
import openai
import os
from ..core.config import settings

# Completely disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"


class VectorService:
    def __init__(self):
        # Initialize ChromaDB client with simpler configuration to avoid tenant issues
        try:
            # First try with PersistentClient
            self.client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            print(f"✅ ChromaDB PersistentClient initialized at: {settings.chroma_persist_directory}")
        except Exception as e:
            print(f"⚠️  PersistentClient failed ({e}), trying simpler Client...")
            try:
                # Fallback to simpler in-memory client
                self.client = chromadb.Client(
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                print("✅ ChromaDB Client (in-memory) initialized")
            except Exception as e2:
                print(f"❌ All ChromaDB clients failed: {e2}")
                raise e2
        
        # Initialize OpenAI client
        openai.api_key = settings.openai_api_key
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get OpenAI embedding for text"""
        try:
            response = openai.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise
    
    def add_document(self, collection_id: str, text: str, metadata: Dict[str, Any]) -> str:
        """Add a document chunk to a collection"""
        try:
            # Get or create collection with custom embedding function
            collection = self.client.get_or_create_collection(
                name=collection_id,
                metadata={"description": f"Document collection for {collection_id}"},
                embedding_function=None  # We'll provide embeddings manually
            )
            
            # Generate unique ID
            doc_id = str(uuid.uuid4())
            
            # Get embedding for the text
            embedding = self._get_embedding(text)
            
            # Add document with embedding
            collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id],
                embeddings=[embedding]
            )
            
            return doc_id
            
        except Exception as e:
            print(f"Error adding document to collection {collection_id}: {e}")
            raise
    
    def search_documents(
        self, 
        collection_id: str, 
        query: str, 
        n_results: int = 5,
        user_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar documents in a collection"""
        try:
            # Get collection
            collection = self.client.get_collection(name=collection_id)
            
            # Get embedding for the query
            query_embedding = self._get_embedding(query)
            
            # Prepare search parameters
            search_params = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            
            # Add user filter if provided
            if user_filter:
                search_params["where"] = user_filter
            
            # Search
            results = collection.query(**search_params)
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
            
        except Exception as e:
            print(f"Error searching collection {collection_id}: {e}")
            return {
                "documents": [],
                "metadatas": [],
                "distances": [],
                "ids": []
            }
    
    def delete_document_collection(self, collection_id: str):
        """Delete an entire document collection"""
        try:
            self.client.delete_collection(name=collection_id)
        except Exception as e:
            print(f"Error deleting collection {collection_id}: {e}")
    
    def get_collection_info(self, collection_id: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            collection = self.client.get_collection(name=collection_id)
            count = collection.count()
            return {
                "name": collection_id,
                "count": count,
                "metadata": collection.metadata
            }
        except Exception as e:
            print(f"Error getting collection info for {collection_id}: {e}")
            return {"name": collection_id, "count": 0, "metadata": {}}
    
    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []
    
    def get_user_collections(self, user_id: int) -> List[str]:
        """Get all collections for a specific user"""
        try:
            all_collections = self.list_collections()
            user_collections = []
            
            for collection_name in all_collections:
                try:
                    collection = self.client.get_collection(name=collection_name)
                    # Check if collection has documents from this user
                    results = collection.get(
                        where={"user_id": user_id},
                        limit=1
                    )
                    if results['documents']:
                        user_collections.append(collection_name)
                except Exception:
                    continue
            
            return user_collections
            
        except Exception as e:
            print(f"Error getting user collections for user {user_id}: {e}")
            return []
    
    def delete_user_documents(self, user_id: int, document_id: int):
        """Delete all chunks for a specific user's document"""
        try:
            collection_id = f"doc_{document_id}"
            collection = self.client.get_collection(name=collection_id)
            
            # Get all document IDs for this user and document
            results = collection.get(
                where={"user_id": user_id, "document_id": document_id}
            )
            
            if results['ids']:
                collection.delete(ids=results['ids'])
                
            # If collection is empty, delete it
            if collection.count() == 0:
                self.client.delete_collection(name=collection_id)
                
        except Exception as e:
            print(f"Error deleting user documents for user {user_id}, document {document_id}: {e}")
    
    def search_all_user_documents(
        self, 
        user_id: int, 
        query: str, 
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search across all of a user's documents"""
        try:
            user_collections = self.get_user_collections(user_id)
            all_results = []
            
            for collection_name in user_collections:
                try:
                    results = self.search_documents(
                        collection_id=collection_name,
                        query=query,
                        n_results=n_results // len(user_collections) + 1,
                        user_filter={"user_id": user_id}
                    )
                    
                    # Process results
                    if results.get('documents') and results['documents'][0]:
                        for i, doc in enumerate(results['documents'][0]):
                            result = {
                                "document": doc,
                                "distance": results.get('distances', [[1.0]])[0][i],
                                "metadata": results.get('metadatas', [{}])[0][i],
                                "collection": collection_name
                            }
                            all_results.append(result)
                            
                except Exception as e:
                    print(f"Error searching collection {collection_name}: {e}")
                    continue
            
            # Sort by distance (relevance)
            all_results.sort(key=lambda x: x['distance'])
            
            return all_results[:n_results]
            
        except Exception as e:
            print(f"Error searching all user documents for user {user_id}: {e}")
            return []
    
    def get_document_stats(self, document_id: int, user_id: int) -> Dict[str, Any]:
        """Get statistics for a specific document"""
        try:
            collection_id = f"doc_{document_id}"
            collection = self.client.get_collection(name=collection_id)
            
            # Get all chunks for this document
            results = collection.get(
                where={"user_id": user_id, "document_id": document_id}
            )
            
            return {
                "document_id": document_id,
                "chunk_count": len(results['documents']),
                "total_characters": sum(len(doc) for doc in results['documents']),
                "collection_id": collection_id
            }
            
        except Exception as e:
            print(f"Error getting document stats for document {document_id}: {e}")
            return {
                "document_id": document_id,
                "chunk_count": 0,
                "total_characters": 0,
                "collection_id": f"doc_{document_id}"
            } 