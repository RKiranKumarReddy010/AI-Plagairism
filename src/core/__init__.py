from .preprocessor import TextPreprocessor
from .chunker import DocumentChunker, DocumentStructure, ParagraphChunk, SentenceChunk

# Backwards compatibility alias
DocumentChunk = DocumentStructure

__all__ = ["TextPreprocessor", "DocumentChunker", "DocumentStructure", "DocumentChunk", "ParagraphChunk", "SentenceChunk"]

