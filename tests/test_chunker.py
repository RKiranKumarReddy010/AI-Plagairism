import unittest
from src.core.chunker import DocumentChunker


class TestDocumentChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = DocumentChunker()

    def test_sentence_split_with_abbreviations(self):
        para = "Dr. Smith and Prof. Jones visited e.g. the laboratory. They arrived at 10 a.m. promptly."
        sentences = self.chunker.split_sentences(para)
        self.assertEqual(len(sentences), 2)
        self.assertIn("Dr. Smith", sentences[0])
        self.assertIn("They arrived", sentences[1])

    def test_missing_period_spaces(self):
        para = "The conclusion was supported by realistic observations.For instance, the result was clear."
        sentences = self.chunker.split_sentences(para)
        self.assertEqual(len(sentences), 2)

    def test_full_document_parsing(self):
        doc_text = """This is the first paragraph. It contains multiple sentences for testing.

This is the second paragraph. It describes a completely different concept. Furthermore, it has a third sentence."""

        doc = self.chunker.parse_document(doc_text)
        self.assertEqual(doc.total_paragraphs, 2)
        self.assertEqual(len(doc.paragraphs[0].sentences), 2)
        self.assertEqual(len(doc.paragraphs[1].sentences), 3)
        self.assertEqual(doc.total_sentences, 5)
        self.assertGreater(doc.total_words, 20)

    def test_reassemble(self):
        sents = [
            ["Sentence one.", "Sentence two."],
            ["Paragraph two sentence one.", "Paragraph two sentence two."]
        ]
        reassembled = self.chunker.reassemble(sents)
        self.assertIn("Sentence one. Sentence two.", reassembled)
        self.assertIn("\n\n", reassembled)


if __name__ == "__main__":
    unittest.main()
