from typing import Dict, Any, List, Optional
from ..core.preprocessor import preprocessor
from ..core.chunker import DocumentChunker
from ..detector.ai_detector import AITextDetector
from ..detector.doc_analyzer import DocumentAnalyzer
from ..rectifier.text_rectifier import TextRectifier
from ..plagiarism.winnowing import WinnowingEngine
from ..plagiarism.semantic import SemanticEngine
from ..config import Config


class DocumentService:
    """Unified orchestration service coordinating AI detection,

    hierarchical document scanning, exact & semantic plagiarism detection,
    and premium text rectification.
    """

    def __init__(self):
        self.chunker = DocumentChunker()
        self.detector = AITextDetector()
        self.analyzer = DocumentAnalyzer(detector=self.detector, chunker=self.chunker)
        self.rectifier = TextRectifier(detector=self.detector, chunker=self.chunker)
        self.winnowing = WinnowingEngine(k=Config.WINNOWING_K, w=Config.WINNOWING_W)
        self.semantic = SemanticEngine(model_name=Config.SEMANTIC_MODEL_NAME)

    def build_report(self, analysis: Dict[str, Any]) -> str:
        """Constructs human-readable diagnostic report."""
        score = analysis.get("ai_score", 0)
        verdict = analysis.get("verdict", "UNKNOWN")
        metrics = analysis.get("metrics", {})
        reasons = analysis.get("reasons", [])

        lines = [f"Verdict: {verdict} (confidence: {score}%)"]

        if metrics.get("word_count"):
            lines.append(f"Word count: {metrics['word_count']}")
        if metrics.get("sentence_count"):
            lines.append(f"Sentences analyzed: {metrics['sentence_count']}")
        if metrics.get("burstiness_cv") is not None:
            lines.append(f"Burstiness CV: {metrics['burstiness_cv']:.3f} (human ~0.7+, AI ~0.3-0.4)")
        if metrics.get("type_token_ratio") is not None:
            lines.append(f"Type-token ratio: {metrics['type_token_ratio']:.3f}")

        ai_markers = metrics.get("ai_markers_found", [])
        human_markers = metrics.get("human_markers_found", [])
        if ai_markers:
            lines.append(f"AI markers found: {', '.join(ai_markers[:10])}")
        if human_markers:
            lines.append(f"Human markers found: {', '.join(human_markers[:10])}")

        if reasons:
            lines.append("")
            lines.append("Reasons:")
            for r in reasons[:6]:
                lines.append(f"  - {r}")

        return "\n".join(lines)

    def build_fix_tips(self, analysis: Dict[str, Any], raw_text: str) -> List[str]:
        """Builds actionable humanization suggestions."""
        metrics = analysis.get("metrics", {})
        tips = []

        cv = metrics.get("burstiness_cv", 0)
        if cv < 0.5:
            tips.append("Vary your sentence lengths. Mix short punchy sentences with longer descriptive ones.")

        ttr = metrics.get("type_token_ratio", 0)
        if ttr > 0.75:
            tips.append("Your vocabulary is overly varied. Repeat key terms naturally instead of constantly using formal synonyms.")

        ai_markers = metrics.get("ai_markers_found", [])
        if ai_markers:
            for marker in ai_markers[:6]:
                if marker in self.rectifier.replacement_map:
                    tips.append(f"Replace '{marker}' with '{self.rectifier.replacement_map[marker]}'")

        tips.append("Add conversational discourse markers, personal perspective, or rhetorical phrasing to break robotic cadence.")
        return tips

    def detect_ai(self, raw_text: str, is_premium: bool = False) -> Dict[str, Any]:
        """Backwards-compatible detection method enhanced with premium rectification."""
        analysis = self.detector.analyze(raw_text)
        report = self.build_report(analysis)
        fix_tips = self.build_fix_tips(analysis, raw_text)

        result: Dict[str, Any] = {
            "status": "success",
            "ai_score": analysis["ai_score"],
            "verdict": analysis["verdict"],
            "report": report,
            "metrics": analysis.get("metrics", {}),
            "fix": fix_tips if (is_premium and analysis["ai_score"] >= Config.AI_THRESHOLD_HIGH) else None
        }

        # Premium feature: Deliver actual rectified text!
        if is_premium:
            rectification = self.rectifier.rectify_document(raw_text)
            result["is_premium"] = True
            result["rectified_text"] = rectification["rectified_text"]
            result["rectification_details"] = {
                "original_ai_score": rectification["original_ai_score"],
                "rectified_ai_score": rectification["rectified_ai_score"],
                "score_reduction": rectification["score_reduction"],
                "modifications_count": rectification["modifications_count"],
                "sample_changes": rectification["sentence_comparisons"][:5]
            }
        else:
            result["is_premium"] = False
            result["premium_upgrade_hint"] = "Upgrade to Premium to receive complete, automatically rectified humanized text."

        return result

    def scan_full_document(self, raw_text: str, is_premium: bool = False, check_plagiarism: bool = True) -> Dict[str, Any]:
        """Full document hierarchical scan: AI sentence heatmap, overall score,

        and optional plagiarism checks, plus full rectified text for premium members.
        """
        doc_analysis = self.analyzer.analyze_document(raw_text)

        response: Dict[str, Any] = {
            "status": "success",
            "overall_ai_score": doc_analysis["overall_score"],
            "verdict": doc_analysis["verdict"],
            "document_stats": doc_analysis["document_stats"],
            "flagged_ai_sentence_count": doc_analysis["flagged_ai_sentence_count"],
            "flagged_ratio": doc_analysis["flagged_ratio"],
            "paragraph_analysis": doc_analysis["paragraph_analysis"],
            "sentence_heatmap": doc_analysis["sentence_heatmap"],
            "reasons": doc_analysis["reasons"]
        }

        # Check plagiarism against indexed library if requested
        if check_plagiarism and self.winnowing.index:
            winnow_res = self.winnowing.query(raw_text)
            semantic_res = self.semantic.query(raw_text)
            response["plagiarism"] = {
                "exact_matches": winnow_res["matches"],
                "semantic_matches": semantic_res
            }

        # Premium Member Rectification
        if is_premium:
            rectification = self.rectifier.rectify_document(raw_text)
            response["is_premium"] = True
            response["rectified_text"] = rectification["rectified_text"]
            response["rectification_details"] = {
                "original_ai_score": rectification["original_ai_score"],
                "rectified_ai_score": rectification["rectified_ai_score"],
                "score_reduction": rectification["score_reduction"],
                "modifications_count": rectification["modifications_count"],
                "sentence_comparisons": rectification["sentence_comparisons"]
            }
        else:
            response["is_premium"] = False
            response["rectified_text"] = None
            response["premium_notice"] = "Full document rectification is an exclusive premium feature."

        return response

    def rectify_document(self, raw_text: str) -> Dict[str, Any]:
        """Dedicated rectification endpoint logic."""
        return self.rectifier.rectify_document(raw_text)

    def index_reference_document(self, doc_id: str, text: str):
        """Indexes a reference document for plagiarism detection."""
        self.winnowing.index_document(doc_id, text)
        self.semantic.index_document(doc_id, text)


doc_service = DocumentService()
