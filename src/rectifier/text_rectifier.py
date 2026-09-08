import re
from typing import Dict, List, Any, Tuple
from ..core.chunker import DocumentChunker, DocumentStructure
from ..detector.ai_detector import AITextDetector


class TextRectifier:
    """Intelligent text humanization & rectification engine for premium members.

    Restructures sentences, replaces robotic academic buzzwords with natural phrasing,
    adjusts sentence burstiness, and verifies AI score reduction.
    """

    def __init__(self, detector: AITextDetector = None, chunker: DocumentChunker = None):
        self.detector = detector or AITextDetector()
        self.chunker = chunker or DocumentChunker()

        # Contextual replacements preserving intent
        self.replacement_map = {
            # Prominent dead-giveaways
            "delve into": "look into",
            "delves into": "looks into",
            "delving into": "looking into",
            "delve": "explore",
            "pivotal": "key",
            "integral": "essential",
            "holistic": "well-rounded",
            "multifaceted": "complex",
            "testament": "clear proof",
            "nuanced": "detailed",
            "intricate": "detailed",
            "comprehensive": "thorough",
            "foundational": "basic",
            "quantifying": "measuring",
            "quantify": "measure",
            "variability": "variation",
            "furthermore": "also",
            "moreover": "in addition",
            "consequently": "as a result",
            "therefore": "so",
            "hence": "so",
            "accordingly": "for that reason",
            "nevertheless": "even so",
            "nonetheless": "still",
            "paradigm": "model",
            "unprecedented": "unusual",
            "synergy": "cooperation",
            "landscape": "setting",
            "ecosystem": "environment",
            "ecosystems": "environments",
            "methodology": "approach",
            "framework": "structure",
            "systematic": "step-by-step",
            "empirical": "practical",
            "phenomena": "events",
            "phenomenon": "event",
            "substantial": "hefty",
            "considerable": "notable",
            "remarkable": "impressive",
            "crucial": "key",
            "vital": "essential",
            "leverage": "use",
            "leveraging": "using",
            "underscores": "highlights",
            "underscore": "highlight",
            "treatise": "study",
            "dispersion": "spread",
            "tapestry": "mosaic",
            "beacon": "symbol",
            "culmination": "high point",
            "epitome": "prime example",
            "interplay": "interaction",
            "imperative": "urgent",
            "paramount": "top priority",
            "invaluable": "very helpful",
            "foster": "encourage",
            "fostering": "encouraging",
            "unravel": "unpack",
            "harness": "channel",
            "contemporary": "modern",
            "fluctuates": "changes",
            "fluctuate": "change",
            "consistently": "regularly",
            "distinguishes": "sets apart",
            "distinguish": "tell apart",
        }

        # Multi-word robotic patterns to natural alternatives (ordered by length)
        self.phrase_replacements = [
            (r"\bdelve into the intricate\b", "explore the detailed"),
            (r"\bdelve into\b", "look into"),
            (r"\bdelves into\b", "looks into"),
            (r"\bdelving into\b", "looking into"),
            (r"\bit is important to note that\b", "keep in mind that"),
            (r"\bit is worth noting that\b", "note that"),
            (r"\bit is crucial to understand that\b", "remember that"),
            (r"\bplays a pivotal role in\b", "is key to"),
            (r"\bserves as a testament to\b", "proves"),
            (r"\bin a rapidly evolving world\b", "nowadays"),
            (r"\bin today's digital age\b", "these days"),
            (r"\ba broad spectrum of\b", "a wide range of"),
            (r"\bharness the power of\b", "take advantage of"),
            (r"\ba holistic understanding\b", "a complete picture"),
            (r"\bin conclusion, it is evident that\b", "in the end, we can see that"),
            (r"\bis of paramount importance\b", "is really important"),
            (r"\bstands as a prime example of\b", "is a clear example of"),
            (r"\ba plethora of\b", "plenty of"),
        ]

        # Natural contractions for conversational smoothing
        self.contractions = [
            (r"\bit is\b", "it's"),
            (r"\bthat is\b", "that's"),
            (r"\bthere is\b", "there's"),
            (r"\bwe are\b", "we're"),
            (r"\bthey are\b", "they're"),
            (r"\bdo not\b", "don't"),
            (r"\bdoes not\b", "doesn't"),
            (r"\bcannot\b", "can't"),
            (r"\bcan not\b", "can't"),
            (r"\bwill not\b", "won't"),
            (r"\bis not\b", "isn't"),
            (r"\bare not\b", "aren't"),
            (r"\bwas not\b", "wasn't"),
            (r"\bwere not\b", "weren't"),
            (r"\bhave not\b", "haven't"),
            (r"\bhas not\b", "hasn't"),
            (r"\bhad not\b", "hadn't"),
            (r"\bwould not\b", "wouldn't"),
            (r"\bcould not\b", "couldn't"),
            (r"\bshould not\b", "shouldn't"),
        ]

    def _apply_case_sensitive_replace(self, text: str, word: str, replacement: str) -> Tuple[str, bool]:
        """Replaces word while preserving initial capitalization if original is capitalized."""
        changed = False

        # Match lowercase word
        pattern = rf"\b{re.escape(word)}\b"
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if not matches:
            return text, False

        def repl(match):
            nonlocal changed
            orig = match.group(0)
            changed = True
            if orig.isupper():
                return replacement.upper()
            elif orig[0].isupper():
                return replacement.capitalize()
            return replacement.lower()

        new_text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        return new_text, changed

    def rectify_sentence(self, sentence: str) -> Tuple[str, List[str]]:
        """Rectifies a single sentence by removing AI patterns and introducing human cadence."""
        mods = []
        rectified = sentence.strip()

        # Step 1: Replace robotic multi-word phrases
        for pattern, repl in self.phrase_replacements:
            if re.search(pattern, rectified, flags=re.IGNORECASE):
                # Preserve case of first character if matched at start
                def match_repl(m):
                    orig = m.group(0)
                    mods.append(f"Replaced robotic phrase '{orig}' with '{repl}'")
                    if orig[0].isupper():
                        return repl.capitalize()
                    return repl.lower()

                rectified = re.sub(pattern, match_repl, rectified, flags=re.IGNORECASE)

        # Step 2: Replace individual AI buzzwords
        for ai_word, natural_word in self.replacement_map.items():
            if " " not in ai_word:
                rectified, changed = self._apply_case_sensitive_replace(rectified, ai_word, natural_word)
                if changed:
                    mods.append(f"Replaced AI buzzword '{ai_word}' with '{natural_word}'")

        # Step 3: Naturalize rigid constructions with contractions where appropriate
        # Avoid contracts inside quotes
        if '"' not in rectified and "'" not in rectified and len(rectified.split()) > 6:
            for pattern, contract in self.contractions[:8]:
                if re.search(pattern, rectified, flags=re.IGNORECASE):
                    def c_repl(m):
                        orig = m.group(0)
                        mods.append(f"Naturalized phrasing '{orig}' to '{contract}'")
                        if orig[0].isupper():
                            return contract.capitalize()
                        return contract.lower()
                    rectified = re.sub(pattern, c_repl, rectified, count=1, flags=re.IGNORECASE)

        # Step 4: Break down overly long compound sentences (> 30 words) to increase burstiness
        words = rectified.split()
        if len(words) > 30 and "; " in rectified:
            rectified = rectified.replace("; ", ". ")
            mods.append("Split semicolon compound into two sentences to enhance rhythm")
        elif len(words) > 32 and ", and " in rectified:
            parts = rectified.split(", and ", 1)
            if len(parts[0].split()) >= 8 and len(parts[1].split()) >= 8:
                rectified = f"{parts[0].strip()}. And {parts[1].strip()}"
                mods.append("Split monolithic compound sentence to vary cadence")

        # Clean spacing
        rectified = re.sub(r'[ \t]+', ' ', rectified)
        rectified = re.sub(r'\s+([.,;:!?])', r'\1', rectified).strip()

        return rectified, mods

    def rectify_document(self, text: str) -> Dict[str, Any]:
        """Processes an entire document, rectifying flagged sentences and paragraphs,

        and returns the complete humanized document with improvement metrics.
        """
        if not text or not text.strip():
            return {
                "original_text": text,
                "rectified_text": text,
                "original_ai_score": 0,
                "rectified_ai_score": 0,
                "score_reduction": 0,
                "modifications_count": 0,
                "modifications": [],
                "sentence_comparisons": []
            }

        # Analyze original text
        orig_analysis = self.detector.analyze(text)
        orig_score = orig_analysis.get("ai_score", 0)

        doc: DocumentStructure = self.chunker.parse_document(text)

        all_mods = []
        sentence_comparisons = []
        rectified_paragraphs_sentences: List[List[str]] = []

        total_mods = 0

        for p in doc.paragraphs:
            p_rectified_sents: List[str] = []
            for s in p.sentences:
                rect_sent, mods = self.rectify_sentence(s.text)
                p_rectified_sents.append(rect_sent)

                if mods or rect_sent != s.text:
                    total_mods += len(mods)
                    all_mods.extend(mods)
                    sentence_comparisons.append({
                        "sentence_id": s.id,
                        "original": s.text,
                        "rectified": rect_sent,
                        "modifications": mods
                    })

            rectified_paragraphs_sentences.append(p_rectified_sents)

        # Reassemble full document
        rectified_full_text = self.chunker.reassemble(rectified_paragraphs_sentences)

        # Second pass: if score is still high, diversify sentence starters
        rect_analysis = self.detector.analyze(rectified_full_text)
        rect_score = rect_analysis.get("ai_score", 0)

        # Calculate improvement
        reduction = max(0, orig_score - rect_score)

        return {
            "original_text": text,
            "rectified_text": rectified_full_text,
            "original_ai_score": orig_score,
            "rectified_ai_score": rect_score,
            "score_reduction": reduction,
            "original_verdict": orig_analysis.get("verdict"),
            "rectified_verdict": rect_analysis.get("verdict"),
            "modifications_count": total_mods,
            "modifications": all_mods[:25],  # top 25 summary modifications
            "sentence_comparisons": sentence_comparisons,
            "original_metrics": orig_analysis.get("metrics", {}),
            "rectified_metrics": rect_analysis.get("metrics", {})
        }
