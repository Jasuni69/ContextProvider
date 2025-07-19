import os
import uuid
import pandas as pd
import fitz  # PyMuPDF
from typing import List, Tuple
from ..core.config import settings


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 200
    
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
        
        # Add each row as readable text
        for index, row in df.iterrows():
            text_content += f"\nRow {index + 1}:\n"
            for col in df.columns:
                text_content += f"  {col}: {row[col]}\n"
            
            # Break after reasonable number of rows to avoid huge files
            if index >= 100:  # Limit to first 100 rows
                text_content += f"\n... (showing first 100 rows of {len(df)} total rows)"
                break
        
        return text_content
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text
    
    def chunk_text(self, text: str, file_type: str = None) -> List[str]:
        """
        Create text chunks using intelligent sentence-aware splitting
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        # Split into sentences first (simple approach)
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size, finalize current chunk
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from the end of previous chunk
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + sentence
            else:
                current_chunk += sentence
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting based on punctuation"""
        import re
        # Split on sentence endings, keeping the punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() + ' ' for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to get overlap at word boundary
        overlap = text[-self.chunk_overlap:]
        space_index = overlap.find(' ')
        if space_index != -1:
            return overlap[space_index:] + ' '
        return overlap + ' ' 