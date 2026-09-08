import hashlib
import re
from typing import List, Set, Tuple, Dict
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# =====================================================================
# ENGINE 1: WINNOWING ALGORITHM (Lexical / Exact Substring Match)
# =====================================================================
class WinnowingEngine:
    def __init__(self, k: int = 5, w: int = 4):
        """
        k: Shingle size (number of words in an n-gram)
        w: Window size for winnowing minimum hash selection
        Guarantee: Catches any verbatim match of length >= (w + k - 1) words
        """
        self.k = k
        self.w = w
        # Inverted index: hash -> set of (doc_id, position)
        self.index: Dict[int, Set[Tuple[str, int]]] = {}
        self.doc_lengths: Dict[str, int] = {}

    def _tokenize(self, text: str) -> List[str]:
        # Normalize: lowercase, strip punctuation
        return re.findall(r"\b\w+\b", text.lower())

    def _hash_shingle(self, shingle: List[str]) -> int:
        joined = " ".join(shingle)
        # 64-bit integer hash using MD5
        return int(hashlib.md5(joined.encode("utf-8")).hexdigest()[:16], 16)

    def fingerprint(self, text: str) -> List[Tuple[int, int]]:
        """Extracts winnowed (hash, position) fingerprints."""
        tokens = self._tokenize(text)
        if len(tokens) < self.k:
            return []

        # 1. Generate k-gram shingles and rolling hashes
        hashes = [
            (self._hash_shingle(tokens[i : i + self.k]), i)
            for i in range(len(tokens) - self.k + 1)
        ]

        # 2. Window minimum selection (Winnowing)
        fingerprints = []
        min_idx = -1

        for i in range(len(hashes) - self.w + 1):
            window = hashes[i : i + self.w]
            # Select minimum hash; rightmost occurrence on ties
            current_min = min(window, key=lambda x: (x[0], -x[1]))

            # Only record when the minimum shifts to avoid duplicate consecutive records
            if min_idx != current_min[1]:
                fingerprints.append(current_min)
                min_idx = current_min[1]

        return fingerprints

    def index_document(self, doc_id: str, text: str):
        tokens = self._tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        fps = self.fingerprint(text)

        for h, pos in fps:
            if h not in self.index:
                self.index[h] = set()
            self.index[h].add((doc_id, pos))

    def query(self, query_text: str) -> Dict[str, float]:
        """Calculates Jaccard similarity coefficient based on shared fingerprints."""
        query_fps = set(h for h, _ in self.fingerprint(query_text))
        if not query_fps:
            return {}

        match_counts: Dict[str, int] = {}
        for h in query_fps:
            if h in self.index:
                for doc_id, _ in self.index[h]:
                    match_counts[doc_id] = match_counts.get(doc_id, 0) + 1

        results = {}
        for doc_id, shared in match_counts.items():
            # Approximate Jaccard similarity across fingerprints
            results[doc_id] = shared / len(query_fps)
        return results