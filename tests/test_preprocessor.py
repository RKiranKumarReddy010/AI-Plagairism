import unittest
from src.core.preprocessor import TextPreprocessor


class TestTextPreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = TextPreprocessor()

    def test_empty_and_none(self):
        self.assertEqual(self.preprocessor.preprocess(""), "")
        self.assertEqual(self.preprocessor.preprocess(None), "")

    def test_latex_cleaning(self):
        latex_text = r"Given $\sigma = 5$ and \textbf{variance} $\mu$, compute $\sum x_i$."
        cleaned = self.preprocessor.preprocess(latex_text)
        self.assertIn("sigma", cleaned)
        self.assertIn("mu", cleaned)
        self.assertIn("variance", cleaned)
        self.assertNotIn(r"\textbf", cleaned)
        self.assertNotIn("$", cleaned)

    def test_unicode_math_and_greek(self):
        math_text = "Let α and β satisfy ∑ x ≤ 10 and ∂y ≠ 0."
        cleaned = self.preprocessor.preprocess(math_text)
        self.assertIn("alpha", cleaned)
        self.assertIn("beta", cleaned)
        self.assertIn("sum", cleaned)
        self.assertIn("less than or equal", cleaned)
        self.assertIn("partial", cleaned)
        self.assertIn("not equal", cleaned)

    def test_smart_punctuation_normalization(self):
        text = "“Smart quotes” and ‘single quotes’ — with an em–dash…"
        cleaned = self.preprocessor.preprocess(text)
        self.assertIn('"Smart quotes"', cleaned)
        self.assertIn("'single quotes'", cleaned)
        self.assertIn(" - ", cleaned)
        self.assertIn("...", cleaned)


if __name__ == "__main__":
    unittest.main()
