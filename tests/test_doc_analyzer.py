import unittest
from src.detector.doc_analyzer import DocumentAnalyzer


class TestDocumentAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = DocumentAnalyzer()

    def test_multi_paragraph_heatmap(self):
        doc_text = """This is an introduction paragraph with simple human observations and thoughts. We found it pretty interesting.

Furthermore, it is important to delve into the comprehensive framework of this phenomenon. Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems."""

        res = self.analyzer.analyze_document(doc_text)
        self.assertEqual(res["document_stats"]["total_paragraphs"], 2)
        self.assertTrue(len(res["sentence_heatmap"]) >= 3)
        self.assertIn("flagged_ai_sentence_count", res)
        self.assertTrue(any(s["is_flagged"] for s in res["sentence_heatmap"]))


if __name__ == "__main__":
    unittest.main()
