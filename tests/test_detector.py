import unittest
from src.detector.ai_detector import AITextDetector


class TestAITextDetector(unittest.TestCase):
    def setUp(self):
        self.detector = AITextDetector()

    def test_short_text_handling(self):
        short = "Hello there friend."
        res = self.detector.analyze(short)
        self.assertEqual(res["verdict"], "TOO SHORT")
        self.assertEqual(res["ai_score"], 0)

    def test_ai_marker_detection(self):
        ai_text = (
            "Furthermore, it is important to delve into the comprehensive framework of this phenomenon. "
            "Moreover, this paradigm serves as a testament to the multifaceted nature of modern systems. "
            "Consequently, the foundational methodology underscores pivotal insights into variability."
        )
        res = self.detector.analyze(ai_text)
        self.assertGreaterEqual(res["ai_score"], 65)
        self.assertEqual(res["verdict"], "LIKELY AI-GENERATED")
        self.assertTrue(len(res["metrics"]["ai_markers_found"]) > 0)

    def test_human_conversational_text(self):
        human_text = (
            "Honestly I kinda don't think that's gonna work out anyway. "
            "We tried it yesterday and it was super weird and honestly pretty terrible. "
            "Maybe we'll check it out tomorrow though, who knows haha."
        )
        res = self.detector.analyze(human_text)
        self.assertLess(res["ai_score"], 45)


if __name__ == "__main__":
    unittest.main()
