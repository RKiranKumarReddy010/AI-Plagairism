from typing import Dict, List, Any
from ..core.chunker import DocumentChunker, DocumentStructure
from .ai_detector import AITextDetector


class DocumentAnalyzer:
    """Enterprise document analyzer capable of processing entire documents of arbitrary length.

    Provides hierarchical paragraph-level and sentence-level heatmaps, overall AI score,
    and granular diagnostic breakdown.
    """

    def __init__(self, detector: AITextDetector = None, chunker: DocumentChunker = None):
        self.detector = detector or AITextDetector()
        self.chunker = chunker or DocumentChunker()

    def analyze_document(self, text: str) -> Dict[str, Any]:
        doc: DocumentStructure = self.chunker.parse_document(text)

        if doc.total_words < 15:
            return {
                "overall_score": 0,
                "verdict": "TOO SHORT",
                "document_stats": {
                    "total_words": doc.total_words,
                    "total_paragraphs": doc.total_paragraphs,
                    "total_sentences": doc.total_sentences
                },
                "paragraph_analysis": [],
                "sentence_heatmap": [],
                "reasons": ["Document too short for reliable statistical evaluation (min 15 words)."],
                "flagged_ai_sentence_count": 0
            }

        sentence_heatmap = []
        flagged_count = 0
        paragraph_analyses = []

        all_sent_scores = []

        for p in doc.paragraphs:
            p_sent_scores = []
            for s in p.sentences:
                s_eval = self.detector.analyze_sentence(s.text)
                score = s_eval["score"]
                all_sent_scores.append(score)
                p_sent_scores.append(score)

                severity = "low"
                if score >= 65:
                    severity = "high"
                    flagged_count += 1
                elif score >= 40:
                    severity = "medium"

                sentence_heatmap.append({
                    "sentence_id": s.id,
                    "paragraph_id": s.paragraph_id,
                    "index_in_para": s.index_in_para,
                    "text": s.text,
                    "ai_score": score,
                    "severity": severity,
                    "is_flagged": score >= 60,
                    "ai_markers": s_eval.get("ai_markers", []),
                    "robotic_phrases": s_eval.get("robotic_phrases", []),
                    "char_start": s.char_start,
                    "char_end": s.char_end
                })

            p_avg = int(round(sum(p_sent_scores) / len(p_sent_scores))) if p_sent_scores else 0
            paragraph_analyses.append({
                "paragraph_id": p.id,
                "word_count": p.word_count,
                "sentence_count": len(p.sentences),
                "ai_score": p_avg,
                "verdict": "HIGH RISK" if p_avg >= 65 else ("MODERATE" if p_avg >= 40 else "CLEAN"),
                "text_preview": p.text[:120] + "..." if len(p.text) > 120 else p.text
            })

        # Also run holistic detector across the full document text
        holistic = self.detector.analyze(doc.cleaned_text)

        # Blended overall score: 50% holistic full-text rhythm + 50% sentence-level aggregation
        # with penalty for high concentrations of AI sentences
        avg_sent_score = sum(all_sent_scores) / len(all_sent_scores) if all_sent_scores else 0
        holistic_score = holistic.get("ai_score", 0)

        flagged_ratio = flagged_count / max(len(doc.all_sentences), 1)
        blended = (holistic_score * 0.5) + (avg_sent_score * 0.3) + (flagged_ratio * 100 * 0.2)
        overall_score = max(0, min(100, int(round(blended))))

        if overall_score >= 65:
            verdict = "LIKELY AI-GENERATED"
        elif overall_score >= 40:
            verdict = "INCONCLUSIVE / MIXED"
        else:
            verdict = "LIKELY HUMAN-WRITTEN"

        return {
            "overall_score": overall_score,
            "verdict": verdict,
            "holistic_analysis": holistic,
            "document_stats": {
                "total_words": doc.total_words,
                "total_paragraphs": doc.total_paragraphs,
                "total_sentences": doc.total_sentences
            },
            "flagged_ai_sentence_count": flagged_count,
            "flagged_ratio": round(flagged_ratio, 4),
            "paragraph_analysis": paragraph_analyses,
            "sentence_heatmap": sentence_heatmap,
            "reasons": holistic.get("reasons", [])
        }
