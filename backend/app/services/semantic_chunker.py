import re
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class SemanticChunker:
    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 200, similarity_threshold: float = 0.5):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.similarity_threshold = similarity_threshold
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Create semantic chunks that respect topic boundaries
        """
        # Split into sentences
        sentences = sent_tokenize(text)
        if len(sentences) <= 1:
            return [text]
        
        # Get sentence embeddings
        embeddings = self.embedding_model.encode(sentences)
        
        # Find topic boundaries
        boundaries = self._find_topic_boundaries(embeddings)
        
        # Create chunks based on boundaries
        chunks = self._create_chunks_from_boundaries(sentences, boundaries)
        
        return chunks
    
    def _find_topic_boundaries(self, embeddings: np.ndarray) -> List[int]:
        """
        Find topic boundaries using cosine similarity between adjacent sentences
        """
        boundaries = [0]  # Always start with first sentence
        
        for i in range(1, len(embeddings)):
            # Calculate similarity with previous sentence
            similarity = cosine_similarity(
                embeddings[i-1].reshape(1, -1),
                embeddings[i].reshape(1, -1)
            )[0][0]
            
            # If similarity drops below threshold, it's likely a topic boundary
            if similarity < self.similarity_threshold:
                boundaries.append(i)
        
        boundaries.append(len(embeddings))  # Always end with last sentence
        return boundaries
    
    def _create_chunks_from_boundaries(self, sentences: List[str], boundaries: List[int]) -> List[str]:
        """
        Create chunks respecting topic boundaries and size constraints
        """
        chunks = []
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            # Get sentences for this topic
            topic_sentences = sentences[start_idx:end_idx]
            topic_text = ' '.join(topic_sentences)
            
            # If topic is small enough, make it one chunk
            if len(topic_text) <= self.max_chunk_size:
                if len(topic_text) >= self.min_chunk_size:
                    chunks.append(topic_text)
            else:
                # Split large topic into smaller chunks while preserving coherence
                sub_chunks = self._split_large_topic(topic_sentences)
                chunks.extend(sub_chunks)
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def _split_large_topic(self, sentences: List[str]) -> List[str]:
        """
        Split a large topic into smaller chunks while maintaining coherence
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed max size, finalize current chunk
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(chunk_text)
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(chunk_text)
        
        return chunks
    
    def chunk_with_headers(self, text: str) -> List[str]:
        """
        Enhanced chunking that recognizes headers and section boundaries
        """
        # Detect common header patterns
        header_patterns = [
            r'^#{1,6}\s+.+$',  # Markdown headers
            r'^[A-Z][A-Z\s]+:?\s*$',  # ALL CAPS headers
            r'^\d+\.\s+[A-Z].+$',  # Numbered sections
            r'^[A-Z][^.!?]*:$',  # Title case with colon
        ]
        
        lines = text.split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is a header
            is_header = any(re.match(pattern, line, re.MULTILINE) for pattern in header_patterns)
            
            if is_header and current_section:
                # Finalize previous section
                sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            sections.append('\n'.join(current_section))
        
        # Apply semantic chunking to each section
        all_chunks = []
        for section in sections:
            if len(section) <= self.max_chunk_size:
                all_chunks.append(section)
            else:
                section_chunks = self.chunk_text(section)
                all_chunks.extend(section_chunks)
        
        return all_chunks


class HybridChunker:
    """
    Combines multiple chunking strategies for optimal results
    """
    def __init__(self):
        self.semantic_chunker = SemanticChunker()
        self.fallback_chunk_size = 1000
        self.fallback_overlap = 200
    
    def chunk_text(self, text: str, document_type: str = 'general') -> List[str]:
        """
        Choose the best chunking strategy based on document type
        """
        try:
            if document_type == 'structured':
                return self.semantic_chunker.chunk_with_headers(text)
            else:
                return self.semantic_chunker.chunk_text(text)
        except Exception as e:
            # Fallback to simple chunking if semantic chunking fails
            print(f"Semantic chunking failed: {e}. Using fallback chunking.")
            return self._fallback_chunk(text)
    
    def _fallback_chunk(self, text: str) -> List[str]:
        """
        Fallback to simple chunking if semantic chunking fails
        """
        if len(text) <= self.fallback_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.fallback_chunk_size
            
            if end < len(text):
                # Try to break at sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Try to break at word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.fallback_overlap if end < len(text) else end
        
        return chunks 