"""PDF parser for PostgreSQL documentation."""

import re
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber

from source_qa.models import DocChunk, TableData


class PDFParser:
    """Generic PDF parser using PyMuPDF and pdfplumber."""
    
    def __init__(self):
        """Initialize PDF parser."""
        self.doc: Optional[fitz.Document] = None
        self.file_path: Optional[Path] = None
    
    def open(self, file_path: Path) -> "PDFParser":
        """Open a PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Self for method chaining
        """
        self.file_path = file_path
        self.doc = fitz.open(file_path)
        return self
    
    def close(self):
        """Close the PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None
    
    def __enter__(self) -> "PDFParser":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    @property
    def page_count(self) -> int:
        """Get total number of pages."""
        return len(self.doc) if self.doc else 0
    
    def extract_text_from_page(
        self, page_num: int, preserve_layout: bool = True
    ) -> str:
        """Extract text from a specific page.
        
        Args:
            page_num: Page number (0-indexed)
            preserve_layout: Whether to preserve layout information
            
        Returns:
            Extracted text
        """
        if not self.doc or page_num >= len(self.doc):
            return ""
        
        page = self.doc[page_num]
        
        if preserve_layout:
            # Use blocks to preserve reading order
            blocks = page.get_text("blocks")
            # Sort by vertical position
            blocks.sort(key=lambda b: (b[1], b[0]))
            texts = [b[4] for b in blocks]
            return "\n".join(texts)
        else:
            return page.get_text()
    
    def extract_tables_from_page(self, page_num: int) -> List[TableData]:
        """Extract tables from a specific page using pdfplumber.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            List of TableData objects
        """
        if not self.file_path:
            return []
        
        tables = []
        with pdfplumber.open(self.file_path) as pdf:
            if page_num < len(pdf.pages):
                page = pdf.pages[page_num]
                page_tables = page.extract_tables()
                
                for table in page_tables:
                    if table:
                        tables.append(TableData(
                            rows=table,
                            page_number=page_num + 1,  # Convert to 1-indexed
                        ))
        
        return tables
    
    def extract_metadata(self) -> dict:
        """Extract PDF metadata."""
        if not self.doc:
            return {}
        
        return {
            "title": self.doc.metadata.get("title", ""),
            "author": self.doc.metadata.get("author", ""),
            "subject": self.doc.metadata.get("subject", ""),
            "creator": self.doc.metadata.get("creator", ""),
            "producer": self.doc.metadata.get("producer", ""),
            "page_count": len(self.doc),
        }
    
    def detect_chapters(self) -> List[Tuple[int, str]]:
        """Detect chapter boundaries and titles.
        
        Returns:
            List of (page_number, chapter_title) tuples
        """
        chapters = []
        
        # Common patterns for chapter titles in technical docs
        chapter_patterns = [
            r'^Chapter\s+\d+[.:]\s+(.+)$',
            r'^\d+\.\s+(.+)$',
            r'^(\d+\.\d+)\s+(.+)$',
        ]
        
        for page_num in range(min(20, self.page_count)):  # Check first 20 pages
            text = self.extract_text_from_page(page_num)
            lines = text.split("\n")
            
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                for pattern in chapter_patterns:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        title = match.group(1) if len(match.groups()) == 1 else match.group(2)
                        chapters.append((page_num, title.strip()))
                        break
        
        return chapters


class PostgreSQLDocParser(PDFParser):
    """Parser specifically designed for PostgreSQL documentation PDFs."""
    
    # PostgreSQL documentation specific settings
    CODE_FONT_NAMES = ["Courier", "CourierNew", "Consolas", "Monospace"]
    HEADING_FONT_SIZES = [24, 20, 18, 16, 14]  # Descending by level
    
    def __init__(self):
        """Initialize PostgreSQL documentation parser."""
        super().__init__()
        self.current_chapter: str = ""
        self.current_section: str = ""
    
    def is_code_block(self, span: dict) -> bool:
        """Check if a text span is code based on font."""
        font = span.get("font", "").lower()
        return any(code_font.lower() in font for code_font in self.CODE_FONT_NAMES)
    
    def extract_code_examples(self, page_num: int) -> List[str]:
        """Extract code examples from a page.
        
        This uses font information to detect code blocks.
        """
        if not self.doc:
            return []
        
        page = self.doc[page_num]
        code_blocks = []
        current_block = []
        
        # Get text with font information
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
            
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    is_code = self.is_code_block(span)
                    
                    if is_code:
                        current_block.append(text)
                    else:
                        if current_block:
                            # End of code block
                            code_text = " ".join(current_block)
                            # Clean up
                            code_text = self._clean_code_block(code_text)
                            if len(code_text) > 10:  # Filter out short fragments
                                code_blocks.append(code_text)
                            current_block = []
        
        # Handle last block
        if current_block:
            code_text = " ".join(current_block)
            code_text = self._clean_code_block(code_text)
            if len(code_text) > 10:
                code_blocks.append(code_text)
        
        return code_blocks
    
    def _clean_code_block(self, text: str) -> str:
        """Clean up extracted code block."""
        # Remove excessive whitespace
        lines = text.split()
        # Join back with single spaces
        text = " ".join(lines)
        # Common cleanup patterns
        text = text.replace("; ", ";\n")  # Put semicolons on their own lines
        text = text.replace("{ ", " {\n")  # Format braces
        text = text.replace(" }", "\n}")
        return text.strip()
    
    def parse_page(self, page_num: int, fast_mode: bool = True) -> DocChunk:
        """Parse a single page into a DocChunk.
        
        Args:
            page_num: Page number (0-indexed)
            fast_mode: If True, skip slow operations like table extraction
            
        Returns:
            DocChunk with extracted content
        """
        text = self.extract_text_from_page(page_num)
        
        # Skip slow operations in fast mode
        if fast_mode:
            tables = []
            code_examples = []
        else:
            tables = self.extract_tables_from_page(page_num)
            code_examples = self.extract_code_examples(page_num)
        
        # Try to detect chapter/section from text
        chapter, section = self._detect_structure(text)
        if chapter:
            self.current_chapter = chapter
        if section:
            self.current_section = section
        
        # Generate chunk ID
        pdf_name = self.file_path.stem if self.file_path else "doc"
        chunk_id = f"doc:{pdf_name}:p{page_num + 1}"
        
        return DocChunk(
            id=chunk_id,
            source_pdf=self.file_path.name if self.file_path else "unknown.pdf",
            chapter=self.current_chapter or "Unknown Chapter",
            section=self.current_section or None,
            page_number=page_num + 1,  # Convert to 1-indexed
            content=text,
            tables=tables,
            code_examples=code_examples,
        )
    
    def _detect_structure(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Detect chapter and section from page text."""
        chapter = None
        section = None
        
        lines = text.split("\n")[:20]  # Check first 20 lines
        
        for line in lines:
            line = line.strip()
            
            # Chapter patterns
            chapter_match = re.match(r'^Chapter\s+\d+[.:]?\s*(.+)', line, re.IGNORECASE)
            if chapter_match:
                chapter = chapter_match.group(1).strip()
                continue
            
            # Section patterns (e.g., "1. Introduction" or "52.1. Overview")
            section_match = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)', line)
            if section_match:
                section = line
                # If this looks like a main section (e.g., "1." not "1.1."), update chapter
                if re.match(r'^\d+\s+', line) and not re.match(r'^\d+\.\d+', line):
                    if not chapter:
                        chapter = section_match.group(2).strip()
        
        return chapter, section
    
    def parse_document(self, chunk_size: int = 5, fast_mode: bool = True) -> Iterator[DocChunk]:
        """Parse entire document into chunks.
        
        Args:
            chunk_size: Number of pages per chunk (for multi-page chunks)
            fast_mode: If True, skip slow operations for faster parsing
            
        Yields:
            DocChunk objects
        """
        if not self.doc:
            return
        
        if chunk_size == 1:
            # Single-page chunks
            for page_num in range(self.page_count):
                yield self.parse_page(page_num, fast_mode=fast_mode)
        else:
            # Multi-page chunks
            current_content = []
            current_tables = []
            current_code = []
            start_page = 0
            
            for page_num in range(self.page_count):
                page_chunk = self.parse_page(page_num, fast_mode=fast_mode)
                current_content.append(page_chunk.content)
                current_tables.extend(page_chunk.tables)
                current_code.extend(page_chunk.code_examples)
                
                if (page_num + 1) % chunk_size == 0 or page_num == self.page_count - 1:
                    # Yield accumulated chunk
                    pdf_name = self.file_path.stem if self.file_path else "doc"
                    chunk_id = f"doc:{pdf_name}:p{start_page + 1}-{page_num + 1}"
                    
                    yield DocChunk(
                        id=chunk_id,
                        source_pdf=page_chunk.source_pdf,
                        chapter=page_chunk.chapter,
                        section=page_chunk.section,
                        page_number=start_page + 1,
                        content="\n\n".join(current_content),
                        tables=current_tables,
                        code_examples=current_code,
                    )
                    
                    # Reset accumulators
                    current_content = []
                    current_tables = []
                    current_code = []
                    start_page = page_num + 1
