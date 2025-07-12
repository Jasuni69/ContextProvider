import os
import uuid
import pandas as pd
import fitz  # PyMuPDF
from typing import List, Tuple
from ..core.config import settings
from .semantic_chunker import HybridChunker


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.semantic_chunker = HybridChunker()
    
    def save_uploaded_file(self, file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """Save uploaded file and return file path and generated filename"""
        file_extension = original_filename.split('.')[-1].lower()
        generated_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.upload_dir, generated_filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path, generated_filename
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text content from different file types"""
        if file_type == "txt":
            return self._extract_from_txt(file_path)
        elif file_type == "csv":
            return self._extract_from_csv(file_path)
        elif file_type == "pdf":
            return self._extract_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        df = pd.read_csv(file_path)
        # Convert DataFrame to a readable text format
        text_content = f"CSV File Content:\n\n"
        text_content += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        text_content += f"Number of rows: {len(df)}\n\n"
        text_content += "Data:\n"
        text_content += df.to_string(index=False)
        return text_content
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        doc = fitz.open(file_path)
        text_content = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text_content += f"\n--- Page {page_num + 1} ---\n"
            text_content += page.get_text()
        
        doc.close()
        return text_content
    
    def chunk_text(self, text: str, file_type: str = 'general') -> List[str]:
        """
        Split text into semantic chunks that respect topic boundaries
        """
        # Determine document type for optimal chunking strategy
        document_type = self._determine_document_type(text, file_type)
        
        # Use semantic chunking
        chunks = self.semantic_chunker.chunk_text(text, document_type)
        
        # Fallback to old method if semantic chunking produces no results
        if not chunks:
            chunks = self._fallback_chunk_text(text)
        
        return chunks
    
    def _determine_document_type(self, text: str, file_type: str) -> str:
        """
        Determine the best chunking strategy based on document characteristics
        """
        # Check for structured document indicators
        structured_indicators = [
            r'^#{1,6}\s+',  # Markdown headers
            r'^\d+\.\s+[A-Z]',  # Numbered sections
            r'^[A-Z][A-Z\s]+:',  # ALL CAPS headers
            r'Chapter \d+',  # Chapter indicators
            r'Section \d+',  # Section indicators
        ]
        
        import re
        for pattern in structured_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return 'structured'
        
        # CSV files are typically structured
        if file_type == 'csv':
            return 'structured'
        
        return 'general'
    
    def _fallback_chunk_text(self, text: str) -> List[str]:
        """
        Fallback to the original chunking method if semantic chunking fails
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap if end < len(text) else end
        
        return chunks
    
    def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        file_size = os.path.getsize(file_path)
        return {
            "size": file_size,
            "exists": os.path.exists(file_path)
        } 