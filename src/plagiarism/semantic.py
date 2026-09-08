import re
from typing import List, Dict, Any, Optional

try:
    import numpy as np
except ImportError:
    np = None

try:
    import faiss
except ImportError:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class SemanticEngine:
    """Semantic vector plagiarism detection using FAISS and SentenceTransformers.

    Detects paraphrased, summarized, and idea-level text overlap.
    Falls back gracefully when vector dependencies are unavailable (e.g. serverless environments).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model: Optional[Any] = None
        self._index: Optional[Any] = None
        self.dim: Optional[int] = None
        self.metadata: List[Dict[str, Any]] = []
        self.indexed_docs: Dict[str, str] = {}

    @property
    def is_available(self) -> bool:
        return SentenceTransformer is not None and faiss is not None

    @property
    def model(self):
        """Lazy load model on first use if available."""
        if not self.is_available:
            return None
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
            self.dim = self._model.get_sentence_embedding_dimension()
            self._index = faiss.IndexFlatIP(self.dim)
        return self._model

    @property
    def index(self):
        if not self.is_available:
            return None
        if self._index is None:
            _ = self.model  # triggers initialization
        return self._index

    def _chunk_text(self, text: str) -> List[str]:
        # Split text into meaningful sentence chunks
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if len(s.split()) >= 4]

    def index_document(self, doc_id: str, text: str):
        """Encodes and indexes chunks of a document into the FAISS index if available."""
        if not self.is_available or self.model is None or self.index is None:
            return

        chunks = self._chunk_text(text)
        if not chunks:
            return

        self.indexed_docs[doc_id] = text
        embeddings = self.model.encode(chunks, convert_to_numpy=True)
        # Normalize to unit length for cosine similarity via inner product
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        for chunk in chunks:
            self.metadata.append({"doc_id": doc_id, "chunk": chunk})

    def query(self, query_text: str, top_k: int = 3, threshold: float = 0.75) -> List[Dict[str, Any]]:
        """Queries the vector index for semantic matches above the similarity threshold."""
        if not self.is_available or self.model is None or self.index is None or self.index.ntotal == 0:
            return []

        query_chunks = self._chunk_text(query_text)
        if not query_chunks:
            return []

        q_embeddings = self.model.encode(query_chunks, convert_to_numpy=True)
        faiss.normalize_L2(q_embeddings)

        effective_top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(q_embeddings, effective_top_k)
        flagged_passages = []

        for i, q_chunk in enumerate(query_chunks):
            for rank in range(effective_top_k):
                score = float(distances[i][rank])
                idx = int(indices[i][rank])
                if score >= threshold and idx != -1 and idx < len(self.metadata):
                    flagged_passages.append({
                        "query_chunk": q_chunk,
                        "matched_doc": self.metadata[idx]["doc_id"],
                        "matched_text": self.metadata[idx]["chunk"],
                        "similarity": round(score, 4)
                    })

        return flagged_passages
