"""Document chunk model for representing parsed PDF content."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TableData:
    """Represents a table extracted from PDF."""
    
    rows: List[List[str]]
    page_number: int
    bbox: Optional[tuple] = None  # Bounding box (x0, y0, x1, y1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows": self.rows,
            "page_number": self.page_number,
            "bbox": self.bbox,
        }


@dataclass
class DocChunk:
    """Represents a chunk of content from PostgreSQL documentation PDF.
    
    Attributes:
        id: Unique identifier (e.g., "docs:internals.pdf:p45:s3.2")
        source_pdf: Source PDF filename
        chapter: Main chapter title
        section: Section/subsection title
        page_number: Page number in PDF
        content: Text content
        tables: Extracted tables
        code_examples: Code examples within this chunk
        related_entities: IDs of related code entities
        embedding: Vector embedding for semantic search
        metadata: Additional metadata (font info, layout, etc.)
    """
    
    id: str
    source_pdf: str
    chapter: str
    section: Optional[str] = None
    page_number: int = 0
    content: str = ""
    tables: List[TableData] = field(default_factory=list)
    code_examples: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_pdf": self.source_pdf,
            "chapter": self.chapter,
            "section": self.section,
            "page_number": self.page_number,
            "content": self.content,
            "tables": [t.to_dict() for t in self.tables],
            "code_examples": self.code_examples,
            "related_entities": self.related_entities,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocChunk":
        """Create from dictionary."""
        tables = [TableData(**t) for t in data.get("tables", [])]
        return cls(
            id=data["id"],
            source_pdf=data["source_pdf"],
            chapter=data["chapter"],
            section=data.get("section"),
            page_number=data.get("page_number", 0),
            content=data.get("content", ""),
            tables=tables,
            code_examples=data.get("code_examples", []),
            related_entities=data.get("related_entities", []),
            metadata=data.get("metadata", {}),
        )
    
    @property
    def full_title(self) -> str:
        """Get full title including chapter and section."""
        if self.section:
            return f"{self.chapter} > {self.section}"
        return self.chapter
    
    def format_for_context(self, include_tables: bool = True) -> str:
        """Format chunk for LLM context."""
        parts = [
            f"## {self.full_title}",
            f"Source: {self.source_pdf}, Page {self.page_number}",
            "",
            self.content,
        ]
        
        if include_tables and self.tables:
            parts.extend(["", "### Tables"])
            for i, table in enumerate(self.tables, 1):
                parts.append(f"\nTable {i}:")
                for row in table.rows:
                    parts.append(" | ".join(row))
        
        if self.code_examples:
            parts.extend(["", "### Code Examples"])
            for i, code in enumerate(self.code_examples, 1):
                parts.extend([f"\nExample {i}:", "```c", code, "```"])
        
        return "\n".join(parts)
