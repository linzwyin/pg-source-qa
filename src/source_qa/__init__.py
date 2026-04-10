"""PostgreSQL Source Code & Documentation QA System.

A professional question-answering system for PostgreSQL internals,
combining source code analysis with official documentation.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"
__description__ = "PostgreSQL Source Code & Documentation QA System"

from source_qa.config import Settings, get_settings
from source_qa.qa_engine import CodeQASystem

__all__ = [
    "CodeQASystem",
    "Settings",
    "get_settings",
    "__version__",
]
