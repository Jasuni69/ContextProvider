from typing import List, Dict, Any, Tuple
import os
from ..core.config import settings

class ChatService:
    def __init__(self):
        self.openai_api_key = settings.openai_api_key
        self.use_openai = bool(self.openai_api_key)
        
        if self.use_openai:
            try:
                import openai
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            except ImportError:
                print("OpenAI package not installed. Using fallback responses.")
                self.use_openai = False
    
    def generate_response(self, query: str, search_results: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Generate a response based on the query and search results
        """
        if not search_results:
            return self._no_results_response(query)
        
        # Extract sources
        sources = []
        context_chunks = []
        
        for result in search_results:
            if result.get('metadata', {}).get('filename'):
                sources.append(result['metadata']['filename'])
            context_chunks.append(result['document'])
        
        # Remove duplicates while preserving order
        sources = list(dict.fromkeys(sources))
        
        if self.use_openai:
            response = self._generate_openai_response(query, context_chunks)
        else:
            response = self._generate_fallback_response(query, context_chunks)
        
        return response, sources
    
    def _generate_openai_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate response using OpenAI"""
        try:
            # Prepare context
            context = "\n\n".join(context_chunks[:3])  # Use top 3 chunks
            
            # Create prompt
            prompt = f"""Based on the following context from uploaded documents, please answer the user's question. If the context doesn't contain relevant information, say so clearly.

Context:
{context}

Question: {query}

Answer:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided document context. Be concise and accurate."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(query, context_chunks)
    
    def _generate_fallback_response(self, query: str, context_chunks: List[str]) -> str:
        """Generate a simple response without OpenAI"""
        
        # Simple keyword matching and response generation
        query_lower = query.lower()
        
        # Find the most relevant chunk
        best_chunk = ""
        best_score = 0
        
        for chunk in context_chunks:
            chunk_lower = chunk.lower()
            # Simple scoring based on keyword matches
            score = sum(1 for word in query_lower.split() if word in chunk_lower)
            if score > best_score:
                best_score = score
                best_chunk = chunk
        
        if best_chunk:
            # Extract a relevant snippet (first 200 characters)
            snippet = best_chunk[:200] + "..." if len(best_chunk) > 200 else best_chunk
            return f"Based on the uploaded documents, here's what I found:\n\n{snippet}"
        else:
            return "I found some relevant information in your documents, but I need more context to provide a specific answer. Could you please rephrase your question or be more specific?"
    
    def _no_results_response(self, query: str) -> Tuple[str, List[str]]:
        """Response when no search results are found"""
        response = "I couldn't find any relevant information in your uploaded documents to answer that question. Please make sure you have uploaded documents that contain information related to your query."
        return response, []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
        
        words = text.lower().split()
        keywords = [word.strip('.,!?;:"()[]{}') for word in words if word.lower() not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords 