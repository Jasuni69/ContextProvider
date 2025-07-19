import os
import uuid
import pandas as pd
import fitz  # PyMuPDF
from typing import List, Tuple
from ..core.config import settings


class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 500  # Reduced from 1000 to prevent token limit issues
        self.chunk_overlap = 100  # Reduced proportionally
    
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
        """Extract text from CSV file with encoding detection and optimized for chunking"""
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
        
        # Create more efficient text representation for large datasets
        text_content = f"CSV Dataset Analysis\n\n"
        text_content += f"Dataset: {os.path.basename(file_path)}\n"
        text_content += f"Columns ({len(df.columns)}): {', '.join(df.columns.tolist())}\n"
        text_content += f"Total Rows: {len(df)}\n\n"
        
        # Add column descriptions and sample data
        text_content += "Column Information:\n"
        for col in df.columns:
            col_info = f"- {col}: "
            
            # Add data type and sample values
            dtype = str(df[col].dtype)
            unique_count = df[col].nunique()
            
            if df[col].dtype in ['object', 'string']:
                # For text columns, show unique values (limited)
                unique_values = df[col].dropna().unique()[:5]
                col_info += f"Text ({unique_count} unique values). Examples: {', '.join(str(v) for v in unique_values)}"
            elif df[col].dtype in ['int64', 'float64']:
                # For numeric columns, show range
                min_val = df[col].min()
                max_val = df[col].max()
                col_info += f"Numeric (range: {min_val} to {max_val})"
            else:
                col_info += f"Type: {dtype}"
                
            text_content += col_info + "\n"
        
        text_content += "\n"
        
        # Add sample data (fewer rows, more manageable)
        sample_size = min(20, len(df))  # Show max 20 rows instead of 100
        text_content += f"Sample Data (first {sample_size} rows):\n\n"
        
        for index in range(sample_size):
            row = df.iloc[index]
            text_content += f"Row {index + 1}:\n"
            for col in df.columns:
                # Handle potential encoding issues and limit cell content length
                cell_value = str(row[col]).encode('utf-8', errors='replace').decode('utf-8')
                # Limit individual cell content to prevent massive values
                if len(cell_value) > 100:
                    cell_value = cell_value[:100] + "..."
                text_content += f"  {col}: {cell_value}\n"
            text_content += "\n"
        
        if len(df) > sample_size:
            text_content += f"... ({len(df) - sample_size} more rows not shown for brevity)\n\n"
        
        # Add summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            text_content += "Numeric Summary:\n"
            for col in numeric_cols[:5]:  # Limit to 5 numeric columns
                mean_val = df[col].mean()
                text_content += f"  {col}: Average = {mean_val:.2f}\n"
            text_content += "\n"
        
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