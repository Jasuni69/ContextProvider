import openai
from typing import List, Tuple, Optional
from ..core.config import settings
from ..services.vector_service import VectorService


class ChatService:
    def __init__(self):
        self.vector_service = VectorService()
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    def get_document_response(self, query: str, document_id: int, user_id: int) -> Tuple[str, float]:
        """Get AI response based on document content"""
        try:
            # Search for relevant chunks in the specific document
            collection_id = f"doc_{document_id}"
            
            search_results = self.vector_service.search_documents(
                collection_id=collection_id,
                query=query,
                n_results=5,
                user_filter={"user_id": user_id}
            )
            
            if not search_results or not search_results.get('documents'):
                return "I couldn't find relevant information in the document to answer your question.", 0.0
            
            # Extract relevant chunks and calculate average relevance
            relevant_chunks = search_results['documents'][0]  # First result set
            distances = search_results.get('distances', [[1.0] * len(relevant_chunks)])[0]
            
            # Convert distances to relevance scores (lower distance = higher relevance)
            relevance_scores = [1.0 - min(dist, 1.0) for dist in distances]
            avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
            
            # Create context from relevant chunks
            context = "\n\n".join(relevant_chunks[:3])  # Use top 3 chunks
            
            # Generate response using OpenAI
            if settings.openai_api_key:
                response = self._generate_openai_response(query, context)
            else:
                response = self._generate_fallback_response(query, context)
            
            return response, avg_relevance
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your question: {str(e)}", 0.0
    
    def get_general_response(self, query: str) -> str:
        """Get general AI response without document context"""
        try:
            if settings.openai_api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant. Provide clear, concise, and accurate responses."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                return self._generate_general_fallback_response(query)
                
        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _generate_openai_response(self, query: str, context: str) -> str:
        """Generate response using OpenAI GPT-3.5-turbo"""
        try:
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided document context. 
            Use only the information from the provided context to answer questions. 
            If the context doesn't contain enough information to answer the question, say so clearly.
            Be concise but thorough in your responses."""
            
            user_prompt = f"""Context from documents:
{context}

Question: {query}

Please answer the question based on the provided context."""

            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate fallback response when OpenAI is not available"""
        # Simple keyword-based response generation
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Check if query keywords appear in context
        query_words = set(query_lower.split())
        context_words = set(context_lower.split())
        
        common_words = query_words.intersection(context_words)
        
        if len(common_words) >= 2:
            # Find sentences containing query keywords
            sentences = context.split('.')
            relevant_sentences = []
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in query_words):
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                return f"Based on the document, here's what I found: {' '.join(relevant_sentences[:2])}"
        
        return "I found some relevant information in the document, but I cannot provide a specific answer without more advanced AI capabilities. Please check the document content directly."
    
    def _generate_general_fallback_response(self, query: str) -> str:
        """Generate general fallback response when OpenAI is not available"""
        return "I'm currently operating in limited mode without access to advanced AI capabilities. Please configure OpenAI API key for better responses, or try asking about specific documents you've uploaded."
    
    def get_conversation_summary(self, messages: List[dict]) -> str:
        """Generate a summary of the conversation for session titles"""
        try:
            if not messages or not settings.openai_api_key:
                return "Chat Session"
            
            # Get first few messages to create a meaningful title
            first_message = messages[0].get('content', '')
            if len(first_message) > 50:
                return first_message[:47] + "..."
            
            return first_message or "Chat Session"
            
        except Exception:
            return "Chat Session" 