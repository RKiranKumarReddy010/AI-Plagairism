import unittest
from src.rectifier.text_rectifier import TextRectifier
from src.detector.ai_detector import AITextDetector


class TestTextRectifier(unittest.TestCase):
    def setUp(self):
        self.detector = AITextDetector()
        self.rectifier = TextRectifier(detector=self.detector)

    def test_rectify_replaces_robotic_patterns(self):
        sentence = "Furthermore, it is important to note that this serves as a testament to pivotal changes."
        rectified, mods = self.rectifier.rectify_sentence(sentence)
        self.assertNotIn("delve", rectified.lower())
        self.assertNotIn("it is important to note that", rectified.lower())
        self.assertNotIn("serves as a testament to", rectified.lower())
        self.assertNotIn("furthermore", rectified.lower())
        self.assertTrue(len(mods) > 0)

    def test_rectify_document_score_reduction(self):
        ai_doc = (
            "Furthermore, it is crucial to delve into the comprehensive framework of this phenomenon. "
            "Moreover, this paradigm serves as a testament to the multifaceted nature of modern ecosystems. "
            "Consequently, the foundational methodology underscores pivotal insights into variability."
        )

        res = self.rectifier.rectify_document(ai_doc)
        self.assertIn("rectified_text", res)
        self.assertGreater(res["original_ai_score"], 60)
        # Rectified score should drop significantly
        self.assertLess(res["rectified_ai_score"], res["original_ai_score"])
        self.assertGreater(res["score_reduction"], 20)
        self.assertTrue(res["modifications_count"] > 0)


if __name__ == "__main__":
    unittest.main()
