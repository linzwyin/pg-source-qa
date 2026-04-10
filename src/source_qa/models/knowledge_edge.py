"""Knowledge edge model for representing relationships between code and documentation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class RelationType(Enum):
    """Types of relationships between entities."""
    
    # Code-to-Code relationships
    CALLS = "calls"                    # Function A calls function B
    CALLED_BY = "called_by"            # Inverse of CALLS
    INCLUDES = "includes"              # File includes header
    INCLUDED_BY = "included_by"        # Inverse of INCLUDES
    USES = "uses"                      # Uses a type/variable
    USED_BY = "used_by"               # Inverse of USES
    IMPLEMENTS = "implements"          # Implements an interface
    IMPLEMENTED_BY = "implemented_by" # Inverse of IMPLEMENTS
    
    # Code-to-Doc relationships
    DOCUMENTED_IN = "documented_in"    # Code entity is documented in doc chunk
    DOCUMENTS = "documents"            # Doc chunk documents code entity
    MENTIONED_IN = "mentioned_in"      # Code entity is mentioned in doc
    MENTIONS = "mentions"              # Doc mentions code entity
    
    # Doc-to-Doc relationships
    RELATED_TO = "related_to"          # Related documentation
    PART_OF = "part_of"                # Section is part of chapter
    CONTAINS = "contains"              # Inverse of PART_OF
    REFERENCES = "references"          # References another section
    REFERENCED_BY = "referenced_by"    # Inverse of REFERENCES
    
    # Semantic relationships
    SIMILAR_TO = "similar_to"          # Semantically similar
    DEPENDS_ON = "depends_on"          # Depends on another component
    DEPENDED_BY = "depended_by"        # Inverse of DEPENDS_ON


@dataclass
class KnowledgeEdge:
    """Represents a relationship between two entities in the knowledge graph.
    
    Attributes:
        source: Source entity ID
        target: Target entity ID
        relation: Type of relationship
        weight: Relationship strength (0.0 - 1.0)
        evidence: Evidence supporting this relationship
        metadata: Additional metadata
    """
    
    source: str
    target: str
    relation: RelationType
    weight: float = 1.0
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate edge after creation."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight must be between 0.0 and 1.0, got {self.weight}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation.value,
            "weight": self.weight,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEdge":
        """Create from dictionary."""
        return cls(
            source=data["source"],
            target=data["target"],
            relation=RelationType(data["relation"]),
            weight=data.get("weight", 1.0),
            evidence=data.get("evidence"),
            metadata=data.get("metadata", {}),
        )
    
    @property
    def id(self) -> str:
        """Generate unique edge ID."""
        return f"{self.source}--{self.relation.value}--{self.target}"
    
    def reverse(self) -> Optional["KnowledgeEdge"]:
        """Get the reverse edge if relation has an inverse."""
        inverse_map = {
            RelationType.CALLS: RelationType.CALLED_BY,
            RelationType.CALLED_BY: RelationType.CALLS,
            RelationType.INCLUDES: RelationType.INCLUDED_BY,
            RelationType.INCLUDED_BY: RelationType.INCLUDES,
            RelationType.USES: RelationType.USED_BY,
            RelationType.USED_BY: RelationType.USES,
            RelationType.IMPLEMENTS: RelationType.IMPLEMENTED_BY,
            RelationType.IMPLEMENTED_BY: RelationType.IMPLEMENTS,
            RelationType.DOCUMENTED_IN: RelationType.DOCUMENTS,
            RelationType.DOCUMENTS: RelationType.DOCUMENTED_IN,
            RelationType.MENTIONED_IN: RelationType.MENTIONS,
            RelationType.MENTIONS: RelationType.MENTIONED_IN,
            RelationType.PART_OF: RelationType.CONTAINS,
            RelationType.CONTAINS: RelationType.PART_OF,
            RelationType.REFERENCES: RelationType.REFERENCED_BY,
            RelationType.REFERENCED_BY: RelationType.REFERENCES,
            RelationType.DEPENDS_ON: RelationType.DEPENDED_BY,
            RelationType.DEPENDED_BY: RelationType.DEPENDS_ON,
        }
        
        inverse = inverse_map.get(self.relation)
        if inverse:
            return KnowledgeEdge(
                source=self.target,
                target=self.source,
                relation=inverse,
                weight=self.weight,
                evidence=self.evidence,
                metadata=self.metadata.copy(),
            )
        return None
