"""
Simple LLM-based Agents

Only 3 agents needed:
- SimpleLLMExtractor: Raw text → Structured data
- SimpleLLMComparator: Compare two properties
- SimpleLLMReporter: Generate report
"""

from .simple_extractor import SimpleLLMExtractor
from .simple_comparator import SimpleLLMComparator
from .simple_reporter import SimpleLLMReporter

__all__ = [
    'SimpleLLMExtractor',
    'SimpleLLMComparator',
    'SimpleLLMReporter'
]
