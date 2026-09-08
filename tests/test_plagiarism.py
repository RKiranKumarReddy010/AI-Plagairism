import unittest
from src.plagiarism.winnowing import WinnowingEngine


class TestWinnowingPlagiarism(unittest.TestCase):
    def setUp(self):
        self.engine = WinnowingEngine(k=4, w=3)

    def test_exact_match_detection(self):
        ref_text = "The quick brown fox jumps over the lazy dog and runs into the wild forest."
        self.engine.index_document("doc_001", ref_text)

        query_text = "Here is an excerpt where the quick brown fox jumps over the lazy dog in the morning."
        res = self.engine.query(query_text)

        self.assertIn("doc_001", res["matches"])
        self.assertGreater(res["matches"]["doc_001"]["similarity"], 0.3)

    def test_no_match(self):
        self.engine.index_document("doc_alpha", "Quantum mechanics explains the behavior of subatomic particles and fields.")
        unrelated = "Baking sourdough bread requires flour, water, salt, yeast, and patience."
        res = self.engine.query(unrelated)
        self.assertEqual(len(res["matches"]), 0)


if __name__ == "__main__":
    unittest.main()
