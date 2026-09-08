import hashlib
import re
from typing import List, Set, Tuple, Dict, Any


class WinnowingEngine:
    """Lexical exact and near-verbatim plagiarism detection engine

    using the Winnowing algorithm (Manber & Schleimer).
    """

    def __init__(self, k: int = 5, w: int = 4):
        """k: Shingle size (number of words in an n-gram)

        w: Window size for winnowing minimum hash selection
        Guarantee: Catches any verbatim match of length >= (w + k - 1) words
        """
        self.k = k
        self.w = w
        # Inverted index: hash -> set of (doc_id, position)
        self.index: Dict[int, Set[Tuple[str, int]]] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.indexed_docs: Dict[str, str] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _hash_shingle(self, shingle: List[str]) -> int:
        joined = " ".join(shingle)
        return int(hashlib.md5(joined.encode("utf-8")).hexdigest()[:16], 16)

    def fingerprint(self, text: str) -> List[Tuple[int, int]]:
        """Extracts winnowed (hash, position) fingerprints."""
        tokens = self._tokenize(text)
        if len(tokens) < self.k:
            return []

        # 1. Generate k-gram shingles and rolling hashes
        hashes = [
            (self._hash_shingle(tokens[i: i + self.k]), i)
            for i in range(len(tokens) - self.k + 1)
        ]

        # 2. Window minimum selection (Winnowing)
        fingerprints = []
        min_idx = -1

        for i in range(len(hashes) - self.w + 1):
            window = hashes[i: i + self.w]
            # Select minimum hash; rightmost occurrence on ties
            current_min = min(window, key=lambda x: (x[0], -x[1]))

            if min_idx != current_min[1]:
                fingerprints.append(current_min)
                min_idx = current_min[1]

        return fingerprints

    def index_document(self, doc_id: str, text: str):
        """Indexes a reference document into the inverted fingerprint index."""
        tokens = self._tokenize(text)
        self.doc_lengths[doc_id] = len(tokens)
        self.indexed_docs[doc_id] = text
        fps = self.fingerprint(text)

        for h, pos in fps:
            if h not in self.index:
                self.index[h] = set()
            self.index[h].add((doc_id, pos))

    def query(self, query_text: str) -> Dict[str, Any]:
        """Calculates Jaccard and overlap similarity across fingerprints."""
        query_fps = self.fingerprint(query_text)
        if not query_fps:
            return {"matches": {}, "shared_hashes": 0, "query_fingerprints": 0}

        query_hashes = set(h for h, _ in query_fps)
        match_counts: Dict[str, int] = {}
        matched_positions: Dict[str, List[int]] = {}

        for h in query_hashes:
            if h in self.index:
                for doc_id, pos in self.index[h]:
                    match_counts[doc_id] = match_counts.get(doc_id, 0) + 1
                    if doc_id not in matched_positions:
                        matched_positions[doc_id] = []
                    matched_positions[doc_id].append(pos)

        results = {}
        for doc_id, shared in match_counts.items():
            similarity = shared / len(query_hashes)
            results[doc_id] = {
                "similarity": round(similarity, 4),
                "shared_fingerprints": shared,
                "total_query_fingerprints": len(query_hashes),
                "matched_positions": sorted(matched_positions[doc_id])[:10]
            }

        return {
            "matches": results,
            "shared_hashes": sum(match_counts.values()),
            "query_fingerprints": len(query_hashes)
        }
