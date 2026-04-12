"""Code parsing utilities using Tree-sitter."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CodeChunk:
    """Represents a chunk of source code."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    chunk_type: str = "code"  # code, docstring, comment


class CodeParser:
    """Parser for source code files."""

    LANGUAGE_MAP = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
    }

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def get_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_MAP.get(ext, "text")

    def parse_file(self, file_path: Path) -> list[CodeChunk]:
        """Parse a file and extract code chunks."""
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        language = self.get_language(str(file_path))
        
        # For now, use simple line-based chunking
        # TODO: Integrate tree-sitter for semantic chunking
        return self._chunk_by_lines(content, str(file_path), language)

    def _chunk_by_lines(
        self, content: str, file_path: str, language: str
    ) -> list[CodeChunk]:
        """Split content into chunks based on line count with optimizations."""
        lines = content.split("\n")
        chunks = []
        
        current_chunk_lines = []
        current_start = 0
        
        for i, line in enumerate(lines):
            # Skip empty lines at chunk boundaries to reduce noise
            stripped = line.strip()
            
            current_chunk_lines.append(line)
            chunk_text = "\n".join(current_chunk_lines)
            
            if len(chunk_text) >= self.chunk_size:
                # Clean up: remove trailing empty lines
                while current_chunk_lines and not current_chunk_lines[-1].strip():
                    current_chunk_lines.pop()
                
                if current_chunk_lines:  # Only add if there's content
                    chunks.append(
                        CodeChunk(
                            content="\n".join(current_chunk_lines),
                            file_path=file_path,
                            start_line=current_start + 1,
                            end_line=i + 1,
                            language=language,
                        )
                    )
                
                # Keep overlap lines for context (skip empty lines)
                overlap_lines = []
                overlap_count = 0
                for l in reversed(current_chunk_lines):
                    if overlap_count >= self.chunk_overlap // 20:  # Reduced overlap
                        break
                    overlap_lines.insert(0, l)
                    if l.strip():
                        overlap_count += 1
                
                current_chunk_lines = overlap_lines
                current_start = i - len(overlap_lines) + 1
        
        # Add remaining lines (clean up trailing empty lines)
        while current_chunk_lines and not current_chunk_lines[-1].strip():
            current_chunk_lines.pop()
            
        if current_chunk_lines:
            chunks.append(
                CodeChunk(
                    content="\n".join(current_chunk_lines),
                    file_path=file_path,
                    start_line=current_start + 1,
                    end_line=len(lines),
                    language=language,
                )
            )
        
        return chunks

    def extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from a source file."""
        metadata = {
            "file_path": str(file_path),
            "language": self.get_language(str(file_path)),
            "file_name": file_path.name,
        }
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            metadata["line_count"] = len(content.split("\n"))
            metadata["size_bytes"] = len(content.encode("utf-8"))
        except Exception:
            metadata["line_count"] = 0
            metadata["size_bytes"] = 0
        
        return metadata
