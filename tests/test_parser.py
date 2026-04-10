"""Tests for code parser module."""

import tempfile
from pathlib import Path

import pytest

from source_qa.parser import CodeChunk, CodeParser


class TestCodeParser:
    """Test cases for CodeParser."""

    def test_get_language_python(self):
        """Test language detection for Python files."""
        parser = CodeParser()
        assert parser.get_language("test.py") == "python"
        assert parser.get_language("/path/to/file.py") == "python"

    def test_get_language_javascript(self):
        """Test language detection for JavaScript files."""
        parser = CodeParser()
        assert parser.get_language("test.js") == "javascript"
        assert parser.get_language("test.jsx") == "javascript"
        assert parser.get_language("test.ts") == "typescript"
        assert parser.get_language("test.tsx") == "typescript"

    def test_get_language_unknown(self):
        """Test language detection for unknown extensions."""
        parser = CodeParser()
        assert parser.get_language("test.xyz") == "text"

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = CodeParser()
        chunks = parser.parse_file(Path("/nonexistent/file.py"))
        assert chunks == []

    def test_parse_simple_python_file(self):
        """Test parsing a simple Python file."""
        parser = CodeParser(chunk_size=100, chunk_overlap=10)
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def hello():\n    print('Hello')\n")
            temp_path = Path(f.name)
        
        try:
            chunks = parser.parse_file(temp_path)
            assert len(chunks) > 0
            assert chunks[0].language == "python"
            assert chunks[0].file_path == str(temp_path)
        finally:
            temp_path.unlink()

    def test_chunk_by_lines(self):
        """Test line-based chunking."""
        parser = CodeParser(chunk_size=50, chunk_overlap=10)
        
        content = "line1\nline2\nline3\nline4\nline5"
        chunks = parser._chunk_by_lines(content, "test.py", "python")
        
        assert len(chunks) > 0
        assert all(isinstance(c, CodeChunk) for c in chunks)
        assert chunks[0].language == "python"

    def test_extract_metadata(self):
        """Test metadata extraction."""
        parser = CodeParser()
        
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("def test():\n    pass\n")
            temp_path = Path(f.name)
        
        try:
            metadata = parser.extract_metadata(temp_path)
            assert metadata["file_path"] == str(temp_path)
            assert metadata["language"] == "python"
            assert metadata["file_name"] == temp_path.name
            assert metadata["line_count"] == 2
        finally:
            temp_path.unlink()
