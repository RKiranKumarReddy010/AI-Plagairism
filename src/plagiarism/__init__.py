"""Plagiarism detection engines: Winnowing (exact) & FAISS Semantic (paraphrase)."""
from .winnowing import WinnowingEngine
from .semantic import SemanticEngine

__all__ = ["WinnowingEngine", "SemanticEngine"]
