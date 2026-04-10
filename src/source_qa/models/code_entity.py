"""Code entity model for representing parsed PostgreSQL source code elements."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CodeEntityType(Enum):
    """Types of code entities in C source code."""
    
    FUNCTION = "function"
    STRUCT = "struct"
    UNION = "union"
    ENUM = "enum"
    TYPEDEF = "typedef"
    MACRO = "macro"
    VARIABLE = "variable"
    HEADER = "header"
    COMMENT = "comment"
    TYPE_DEF = "type_def"


@dataclass
class CodeEntity:
    """Represents a code entity extracted from PostgreSQL source code.
    
    Attributes:
        id: Unique identifier (e.g., "func:execMain.c:ExecutorRun")
        type: Type of code entity
        name: Entity name (e.g., "ExecutorRun")
        file_path: Relative path from PostgreSQL source root
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)
        content: Complete content of the entity
        signature: For functions: return type + name + params
        docstring: Associated documentation comment
        dependencies: IDs of entities this entity depends on
        callers: IDs of entities that call/use this entity
        embedding: Vector embedding for semantic search
        metadata: Additional metadata (visibility, storage class, etc.)
    """
    
    id: str
    type: CodeEntityType
    name: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    signature: Optional[str] = None
    docstring: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    callers: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entity after creation."""
        if self.start_line > self.end_line:
            raise ValueError(f"start_line ({self.start_line}) cannot be greater than end_line ({self.end_line})")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "signature": self.signature,
            "docstring": self.docstring,
            "dependencies": self.dependencies,
            "callers": self.callers,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeEntity":
        """Create entity from dictionary."""
        return cls(
            id=data["id"],
            type=CodeEntityType(data["type"]),
            name=data["name"],
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            content=data["content"],
            signature=data.get("signature"),
            docstring=data.get("docstring"),
            dependencies=data.get("dependencies", []),
            callers=data.get("callers", []),
            metadata=data.get("metadata", {}),
        )
    
    @property
    def line_count(self) -> int:
        """Return the number of lines in this entity."""
        return self.end_line - self.start_line + 1
    
    @property
    def github_url(self) -> str:
        """Generate GitHub URL for this entity."""
        # Example: https://github.com/postgres/postgres/blob/master/src/backend/executor/execMain.c#L234-L250
        base_url = "https://github.com/postgres/postgres/blob/master"
        return f"{base_url}/{self.file_path}#L{self.start_line}-L{self.end_line}"
    
    def get_preview(self, max_lines: int = 10) -> str:
        """Get a preview of the content (first N lines)."""
        lines = self.content.split("\n")
        if len(lines) <= max_lines:
            return self.content
        return "\n".join(lines[:max_lines]) + "\n..."
