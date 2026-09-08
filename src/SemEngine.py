import hashlib
import re
from typing import List, Set, Tuple, Dict
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# =====================================================================
# ENGINE 2: SEMANTIC FAISS PIPELINE (Paraphrase & Concept Match)
# =====================================================================
class SemanticEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        
        # Inner Product index on L2-normalized vectors calculates Cosine Similarity
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadata: List[Dict] = []

    def _chunk_text(self, text: str) -> List[str]:
        # Split text into meaningful sentence chunks
        sentences = re.split(r"(?<=[.!?]) +", text.strip())
        return [s.strip() for s in sentences if len(s.split()) >= 4]

    def index_document(self, doc_id: str, text: str):
        chunks = self._chunk_text(text)
        if not chunks:
            return

        embeddings = self.model.encode(chunks, convert_to_numpy=True)
        # Normalize to unit length for cosine similarity via inner product
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        for chunk in chunks:
            self.metadata.append({"doc_id": doc_id, "chunk": chunk})

    def query(self, query_text: str, top_k: int = 3, threshold: float = 0.75):
        query_chunks = self._chunk_text(query_text)
        if not query_chunks:
            return []

        q_embeddings = self.model.encode(query_chunks, convert_to_numpy=True)
        faiss.normalize_L2(q_embeddings)

        distances, indices = self.index.search(q_embeddings, top_k)
        flagged_passages = []

        for i, q_chunk in enumerate(query_chunks):
            for rank in range(top_k):
                score = float(distances[i][rank])
                idx = indices[i][rank]
                if score >= threshold and idx != -1:
                    flagged_passages.append({
                        "query_chunk": q_chunk,
                        "matched_doc": self.metadata[idx]["doc_id"],
                        "matched_text": self.metadata[idx]["chunk"],
                        "similarity": round(score, 4)
                    })
        return flagged_passages