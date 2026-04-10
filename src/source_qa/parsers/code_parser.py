"""Code parser for PostgreSQL C source code using Tree-sitter."""

import re
from pathlib import Path
from typing import Iterator, List, Optional

from tree_sitter import Language, Node, Parser, Tree

from source_qa.models import CodeEntity, CodeEntityType


class CodeParser:
    """Generic code parser using Tree-sitter."""
    
    def __init__(self, language_name: str, library_path: Optional[str] = None):
        """Initialize parser for a specific language.
        
        Args:
            language_name: Name of the language (e.g., "c", "cpp")
            library_path: Path to the compiled language library
        """
        self.language_name = language_name
        self.parser = Parser()
        
        # Load language library
        if library_path:
            self.language = Language(library_path, language_name)
        else:
            # Try to load from installed package
            self.language = self._load_builtin_language(language_name)
        
        self.parser.set_language(self.language)
    
    def _load_builtin_language(self, language_name: str) -> Language:
        """Load language from installed tree-sitter-language packages."""
        try:
            if language_name == "c":
                import tree_sitter_c as tstc
                return Language(tstc.language(), "c")
            elif language_name == "cpp":
                import tree_sitter_cpp as tstcpp
                return Language(tstcpp.language(), "cpp")
            else:
                raise ValueError(f"Unsupported language: {language_name}")
        except ImportError as e:
            raise ImportError(
                f"Failed to load language {language_name}. "
                f"Please install tree-sitter-{language_name}: {e}"
            )
    
    def parse_file(self, file_path: Path) -> Tree:
        """Parse a source file and return AST."""
        content = file_path.read_bytes()
        return self.parser.parse(content)
    
    def parse_bytes(self, content: bytes) -> Tree:
        """Parse bytes content and return AST."""
        return self.parser.parse(content)
    
    def extract_text(self, node: Node, source: bytes) -> str:
        """Extract text from a node."""
        return source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
    
    def find_nodes(self, tree: Tree, node_type: str) -> List[Node]:
        """Find all nodes of a specific type in the tree."""
        nodes = []
        
        def traverse(node: Node):
            if node.type == node_type:
                nodes.append(node)
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return nodes


class PostgreSQLCodeParser(CodeParser):
    """Parser specifically designed for PostgreSQL C source code."""
    
    # File patterns to include/exclude
    INCLUDE_PATTERNS = [
        "*.c",
        "*.h",
    ]
    EXCLUDE_PATTERNS = [
        "**/test/**",
        "**/tests/**",
        "**/*_test.c",
        "**/tmp_*",
    ]
    
    # Important directories in PostgreSQL source
    KEY_DIRECTORIES = [
        "src/backend",
        "src/include",
        "src/common",
        "src/port",
    ]
    
    def __init__(self):
        """Initialize PostgreSQL C code parser."""
        super().__init__("c")
    
    def is_pg_source_file(self, file_path: Path) -> bool:
        """Check if file is a PostgreSQL source file we should parse."""
        # Check extension
        if file_path.suffix not in [".c", ".h"]:
            return False
        
        # Check exclude patterns
        str_path = str(file_path)
        for pattern in self.EXCLUDE_PATTERNS:
            # Simple glob matching
            pattern = pattern.replace("**", "*").replace("*", ".*")
            if re.match(pattern, str_path):
                return False
        
        return True
    
    def extract_function(
        self, node: Node, source: bytes, file_path: str
    ) -> Optional[CodeEntity]:
        """Extract a function definition from AST node."""
        if node.type != "function_definition":
            return None
        
        # Get function name
        declarator = node.child_by_field_name("declarator")
        if not declarator:
            return None
        
        func_name = self._extract_function_name(declarator)
        if not func_name:
            return None
        
        # Get function signature
        signature = self._extract_signature(node, source)
        
        # Get docstring (comment before function)
        docstring = self._extract_docstring(node, source)
        
        # Get content
        content = self.extract_text(node, source)
        
        return CodeEntity(
            id=f"func:{file_path}:{func_name}",
            type=CodeEntityType.FUNCTION,
            name=func_name,
            file_path=file_path,
            start_line=node.start_point[0] + 1,  # Convert to 1-indexed
            end_line=node.end_point[0] + 1,
            content=content,
            signature=signature,
            docstring=docstring,
        )
    
    def _extract_function_name(self, declarator: Node) -> Optional[str]:
        """Extract function name from declarator node."""
        # Handle different declarator structures
        if declarator.type == "identifier":
            return declarator.text.decode("utf-8")
        
        if declarator.type == "function_declarator":
            # Get the identifier child
            for child in declarator.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8")
                elif child.type in ["parenthesized_declarator", "pointer_declarator"]:
                    # Handle complex declarators
                    name = self._extract_function_name(child)
                    if name:
                        return name
        
        # Recursively search
        for child in declarator.children:
            if child.type != "parameter_list":
                name = self._extract_function_name(child)
                if name:
                    return name
        
        return None
    
    def _extract_signature(self, node: Node, source: bytes) -> str:
        """Extract function signature (return type + name + params)."""
        # Get everything up to the function body
        body = node.child_by_field_name("body")
        if body:
            # Signature is from start to body start
            signature_bytes = source[node.start_byte:body.start_byte]
            return signature_bytes.decode("utf-8", errors="ignore").strip()
        return self.extract_text(node, source)
    
    def _extract_docstring(self, node: Node, source: bytes) -> Optional[str]:
        """Extract documentation comment preceding the function."""
        # In Tree-sitter, comments are usually separate nodes
        # This is a simplified version - full implementation would scan preceding siblings
        return None
    
    def extract_struct(
        self, node: Node, source: bytes, file_path: str
    ) -> Optional[CodeEntity]:
        """Extract a struct definition from AST node."""
        if node.type not in ["struct_specifier", "type_definition"]:
            return None
        
        # Handle struct specifier
        if node.type == "struct_specifier":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                content = self.extract_text(node, source)
                
                return CodeEntity(
                    id=f"struct:{file_path}:{name}",
                    type=CodeEntityType.STRUCT,
                    name=name,
                    file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    content=content,
                )
        
        # Handle typedef struct
        elif node.type == "type_definition":
            # Complex parsing for typedef
            pass
        
        return None
    
    def extract_macro(
        self, line: str, line_number: int, file_path: str
    ) -> Optional[CodeEntity]:
        """Extract a macro definition from a line of code.
        
        Note: Macros are handled separately because Tree-sitter C parser
        doesn't include preprocessor directives in the AST.
        """
        macro_pattern = r'^\s*#define\s+(\w+)\s*(.*)$'
        match = re.match(macro_pattern, line)
        
        if match:
            name = match.group(1)
            value = match.group(2).strip()
            
            return CodeEntity(
                id=f"macro:{file_path}:{name}",
                type=CodeEntityType.MACRO,
                name=name,
                file_path=file_path,
                start_line=line_number,
                end_line=line_number,
                content=line.strip(),
                signature=f"#define {name} {value}" if value else f"#define {name}",
            )
        
        return None
    
    def parse_pg_file(self, file_path: Path, relative_to: Path) -> List[CodeEntity]:
        """Parse a PostgreSQL source file and extract all entities."""
        if not self.is_pg_source_file(file_path):
            return []
        
        entities = []
        
        try:
            source = file_path.read_bytes()
            tree = self.parse_bytes(source)
            
            # Get relative path for entity IDs
            rel_path = file_path.relative_to(relative_to)
            
            # Extract functions
            func_nodes = self.find_nodes(tree, "function_definition")
            for node in func_nodes:
                entity = self.extract_function(node, source, str(rel_path))
                if entity:
                    entities.append(entity)
            
            # Extract structs
            struct_nodes = self.find_nodes(tree, "struct_specifier")
            for node in struct_nodes:
                entity = self.extract_struct(node, source, str(rel_path))
                if entity:
                    entities.append(entity)
            
            # Extract macros (from raw text)
            text = source.decode("utf-8", errors="ignore")
            for i, line in enumerate(text.split("\n"), 1):
                macro = self.extract_macro(line, i, str(rel_path))
                if macro:
                    entities.append(macro)
        
        except Exception as e:
            # Log error but continue
            print(f"Error parsing {file_path}: {e}")
        
        return entities
    
    def parse_directory(
        self, directory: Path, relative_to: Optional[Path] = None
    ) -> Iterator[CodeEntity]:
        """Parse all PostgreSQL source files in a directory."""
        if relative_to is None:
            relative_to = directory
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                entities = self.parse_pg_file(file_path, relative_to)
                for entity in entities:
                    yield entity
