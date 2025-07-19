import os
import uuid
import pandas as pd
import fitz  # PyMuPDF
from typing import List, Tuple
from ..core.config import settings


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 800  # Increased from 500 to fit more data per chunk
        self.chunk_overlap = 100  # Keep overlap reasonable
    
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
    
    def process_document(self, file_path: str, file_type: str) -> List[str]:
        """
        Complete document processing: extract text and create chunks
        """
        # Extract text from file
        text = self.extract_text_from_file(file_path, file_type)
        
        # Create chunks
        chunks = self.chunk_text(text, file_type)
        
        return chunks
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from CSV file with encoding detection - processes ENTIRE dataset"""
        import chardet
        
        # First, detect the encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result.get('encoding', 'utf-8')
        
        print(f"Detected CSV encoding: {detected_encoding}")
        
        # Try different encodings in order of preference
        encodings_to_try = [
            detected_encoding,
            'utf-8',
            'utf-8-sig',  # UTF-8 with BOM
            'latin1',     # ISO-8859-1
            'cp1252',     # Windows-1252
            'iso-8859-1',
        ]
        
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                print(f"Successfully read CSV with encoding: {encoding}")
                break
            except (UnicodeDecodeError, pd.errors.EmptyDataError) as e:
                print(f"Failed to read CSV with encoding {encoding}: {e}")
                continue
        else:
            # If all encodings fail, try with error handling
            try:
                df = pd.read_csv(file_path, encoding='utf-8', errors='replace')
                print("Read CSV with UTF-8 and error replacement")
            except Exception as e:
                raise ValueError(f"Could not read CSV file with any encoding: {e}")
        
        print(f"Processing CSV with {len(df)} rows and {len(df.columns)} columns")
        
        # Create header information that will be included in every chunk
        header_info = f"CSV Dataset: {os.path.basename(file_path)}\n"
        header_info += f"Total Rows: {len(df)}, Total Columns: {len(df.columns)}\n"
        header_info += f"Columns: {', '.join(df.columns.tolist())}\n\n"
        
        # Convert entire dataframe to text with efficient row-based chunking
        # We'll return the full text and let the chunking function handle splitting
        all_rows_text = header_info
        
        for index, row in df.iterrows():
            row_text = f"Row {index + 1}:\n"
            for col in df.columns:
                # Handle potential encoding issues and limit very long cell values
                cell_value = str(row[col]).encode('utf-8', errors='replace').decode('utf-8')
                # Only truncate extremely long values (>500 chars) to preserve most data
                if len(cell_value) > 500:
                    cell_value = cell_value[:500] + "..."
                row_text += f"{col}: {cell_value}\n"
            row_text += "\n"
            all_rows_text += row_text
            
            # Add progress logging for large datasets
            if (index + 1) % 1000 == 0:
                print(f"Processed {index + 1}/{len(df)} rows")
        
        print(f"Completed CSV text extraction: {len(all_rows_text)} characters")
        return all_rows_text
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with fitz.open(file_path) as pdf:
            for page in pdf:
                text += page.get_text()
        return text
    
    def chunk_text(self, text: str, file_type: str = None) -> List[str]:
        """
        Create text chunks using intelligent splitting, with special handling for CSV data
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        # Special handling for CSV data
        if file_type == "csv":
            return self._chunk_csv_text(text)
        
        # For other file types, use sentence-aware splitting
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
    
    def _chunk_csv_text(self, text: str) -> List[str]:
        """
        Special chunking for CSV data that respects row boundaries
        """
        lines = text.split('\n')
        
        # Extract header information (first few lines before "Row 1:")
        header_lines = []
        data_start_index = 0
        for i, line in enumerate(lines):
            if line.startswith("Row 1:"):
                data_start_index = i
                break
            header_lines.append(line)
        
        header_text = '\n'.join(header_lines) + '\n\n'
        
        chunks = []
        current_chunk = header_text  # Start each chunk with header info
        current_row_lines = []
        
        i = data_start_index
        while i < len(lines):
            line = lines[i]
            
            # Check if this is the start of a new row
            if line.startswith("Row ") and line.endswith(":") and current_row_lines:
                # We've reached a new row, check if adding current row would exceed limit
                row_text = '\n'.join(current_row_lines) + '\n\n'
                
                if len(current_chunk) + len(row_text) > self.chunk_size:
                    # Current chunk is full, save it and start new chunk
                    if current_chunk.strip() != header_text.strip():  # Don't save header-only chunks
                        chunks.append(current_chunk.strip())
                    current_chunk = header_text + row_text
                else:
                    # Add row to current chunk
                    current_chunk += row_text
                
                # Start collecting the new row
                current_row_lines = [line]
            else:
                # Continue collecting lines for current row
                current_row_lines.append(line)
            
            i += 1
        
        # Add the last row if exists
        if current_row_lines:
            row_text = '\n'.join(current_row_lines)
            if len(current_chunk) + len(row_text) > self.chunk_size and current_chunk.strip() != header_text.strip():
                chunks.append(current_chunk.strip())
                current_chunk = header_text + row_text
            else:
                current_chunk += row_text
        
        # Add the final chunk
        if current_chunk.strip() and current_chunk.strip() != header_text.strip():
            chunks.append(current_chunk.strip())
        
        print(f"Created {len(chunks)} chunks from CSV data")
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