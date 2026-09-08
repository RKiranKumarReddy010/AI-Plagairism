import math
import re
import statistics
from typing import Dict, List, Any, Tuple
from ..core.preprocessor import preprocessor


class AITextDetector:
    """Statistical & linguistic multi-signal AI text detector.

    Analyzes cadence burstiness, marker density, lexical diversity,
    and robotic syntactical markers.
    """

    def __init__(self):
        self.stopwords = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
            "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
            "this", "but", "his", "by", "from", "they", "we", "say", "her",
            "she", "or", "an", "will", "my", "one", "all", "would", "there",
            "their", "what", "so", "up", "out", "if", "about", "who", "get",
            "which", "go", "me", "when", "make", "can", "like", "time", "no",
            "just", "him", "know", "take", "is", "are", "was", "were", "between"
        }

        # AI markers with weights
        self.ai_markers: Dict[str, float] = {
            "comprehensive": 2.5, "treatise": 3.0, "dispersion": 1.5,
            "foundational": 2.5, "metric": 1.8, "quantifying": 2.2,
            "variability": 2.0, "furthermore": 2.5, "moreover": 2.2,
            "delve": 3.5, "delves": 3.5, "delving": 3.5,
            "pivotal": 2.8, "integral": 2.2, "holistic": 2.5,
            "multifaceted": 3.0, "testament": 2.8, "nuanced": 2.4,
            "intricate": 2.2, "robust": 1.8, "leverage": 2.2,
            "underscores": 2.2, "underscore": 2.0, "additionally": 2.0,
            "consequently": 2.0, "therefore": 1.6, "thus": 1.4,
            "hence": 1.5, "accordingly": 1.8, "nevertheless": 1.5,
            "nonetheless": 1.3, "specifically": 1.0, "particularly": 1.0,
            "notably": 1.2, "essentially": 1.0, "fundamentally": 1.5,
            "critically": 1.0, "paradigm": 2.5, "unprecedented": 2.2,
            "synergy": 2.5, "landscape": 1.5, "ecosystem": 1.5,
            "methodology": 1.5, "framework": 1.2, "systematic": 1.0,
            "empirical": 1.5, "theoretical": 1.0, "phenomena": 1.2,
            "phenomenon": 1.0, "substantial": 0.8, "considerable": 0.8,
            "remarkable": 0.8, "significant": 0.8, "crucial": 0.8,
            "vital": 0.8, "essential": 0.8, "critical": 0.8,
            "contemporary": 1.2, "statistical": 0.8, "mathematical": 0.8,
            "analytical": 1.0, "quantitative": 1.2, "qualitative": 1.0,
            "distinguish": 1.0, "distinguishes": 1.0, "fluctuates": 1.2,
            "fluctuate": 1.0, "entirely": 1.0, "identical": 1.0,
            "consistently": 1.0, "consistency": 0.8,
            "tapestry": 3.0, "beacon": 2.8, "culmination": 2.5,
            "epitome": 2.5, "interplay": 2.5, "imperative": 2.0,
            "paramount": 2.2, "invaluable": 1.8, "foster": 1.8,
            "fostering": 1.8, "unravel": 2.2, "harness": 1.8
        }

        # Conversational human markers with discount weights
        self.human_markers: Dict[str, float] = {
            "kinda": 2.5, "gonna": 2.2, "wanna": 2.0, "pretty": 1.2,
            "stuff": 1.5, "anyway": 1.4, "honestly": 1.6, "actually": 1.1,
            "btw": 2.5, "imo": 2.5, "weird": 1.5, "cool": 1.5,
            "awesome": 1.5, "amazing": 1.5, "terrible": 1.5,
            "horrible": 1.5, "love": 1.0, "hate": 1.0, "like": 0.5,
            "just": 0.3, "really": 0.3, "super": 1.0, "totally": 1.2,
            "lol": 2.0, "haha": 2.0, "omg": 2.0, "tbh": 2.5,
            "ngl": 2.5, "idk": 2.5, "smh": 2.5, "fwiw": 2.5,
            "i'm": 1.0, "you're": 1.0, "he's": 1.0, "she's": 1.0,
            "it's": 0.5, "we're": 1.0, "they're": 1.0,
            "can't": 1.0, "won't": 1.0, "don't": 1.0, "isn't": 1.0,
            "aren't": 1.0, "wasn't": 1.0, "weren't": 1.0,
            "hasn't": 1.0, "haven't": 1.0, "hadn't": 1.0,
            "doesn't": 1.0, "didn't": 1.0, "couldn't": 1.0,
            "wouldn't": 1.0, "shouldn't": 1.0, "y'all": 2.0,
            "anyhow": 1.2, "nah": 2.0, "yeah": 1.5, "yep": 1.5
        }

        self.robotic_phrases = [
            r"\bit is important to note that\b",
            r"\bit is worth noting that\b",
            r"\bit is crucial to understand that\b",
            r"\bplays a pivotal role in\b",
            r"\bserves as a testament to\b",
            r"\bin a rapidly evolving world\b",
            r"\bin today's digital age\b",
            r"\ba broad spectrum of\b",
            r"\bdelve into the intricate\b",
            r"\bharness the power of\b",
            r"\ba holistic understanding\b",
            r"\bin conclusion, it is evident that\b",
        ]

    def tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    def sentence_split(self, text: str) -> List[str]:
        normalized = re.sub(r'([a-z])([A-Z])', r'\1. \2', text)
        raw = re.split(r'(?<=[.!?])\s+', normalized.strip())
        return [s.strip() for s in raw if len(s.split()) >= 2]

    def calc_burstiness(self, sentences: list) -> Tuple[float, float]:
        """Calculates standard deviation and coefficient of variation of sentence word counts."""
        if len(sentences) < 2:
            return 0.0, 0.0
        lens = [len(s.split()) for s in sentences]
        s_std = statistics.stdev(lens)
        s_mean = statistics.mean(lens)
        cv = s_std / s_mean if s_mean > 0 else 0.0
        return s_std, cv

    def calc_repetition_entropy(self, tokens: list) -> float:
        """Measures lexical richness (Type-Token Ratio)."""
        if not tokens:
            return 0.0
        return len(set(tokens)) / len(tokens)

    def calc_lexical_markers(self, tokens: list) -> Tuple[float, float, List[str], List[str]]:
        ai_hits = [t for t in tokens if t in self.ai_markers]
        human_hits = [t for t in tokens if t in self.human_markers]
        ai_weight = sum(self.ai_markers[t] for t in ai_hits)
        human_weight = sum(self.human_markers[t] for t in human_hits)
        return ai_weight, human_weight, ai_hits, human_hits

    def check_robotic_patterns(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for pattern in self.robotic_phrases:
            match = re.search(pattern, text_lower)
            if match:
                found.append(match.group(0))
        return found

    def analyze_sentence(self, sentence_text: str) -> Dict[str, Any]:
        """Scores an individual sentence for AI probability."""
        clean = preprocessor.preprocess(sentence_text)
        tokens = self.tokenize(clean)
        if len(tokens) < 3:
            return {"score": 10, "is_ai": False, "markers": []}

        ai_hits = [t for t in tokens if t in self.ai_markers]
        human_hits = [t for t in tokens if t in self.human_markers]
        robotic = self.check_robotic_patterns(clean)

        score = 25  # baseline
        if ai_hits:
            score += min(len(ai_hits) * 22, 50)
        if robotic:
            score += len(robotic) * 25
        if human_hits:
            score -= min(len(human_hits) * 20, 40)

        # Uniform sentence penalty (overly long formal sentences without punctuation)
        if len(tokens) > 28 and not human_hits:
            score += 15

        final_score = max(0, min(100, score))
        return {
            "score": final_score,
            "is_ai": final_score >= 60,
            "ai_markers": list(set(ai_hits)),
            "robotic_phrases": robotic
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """Full statistical analysis of a passage of text."""
        clean_text = preprocessor.preprocess(text)
        tokens = self.tokenize(clean_text)
        sentences = self.sentence_split(clean_text)

        if len(tokens) < 15:
            return {
                "ai_score": 0,
                "verdict": "TOO SHORT",
                "reasons": ["Text too short for reliable statistical evaluation (min 15 words)"],
                "metrics": {
                    "word_count": len(tokens),
                    "sentence_count": len(sentences)
                }
            }

        sent_std, burstiness = self.calc_burstiness(sentences)
        ttr = self.calc_repetition_entropy(tokens)
        ai_weight, human_weight, ai_hits, human_hits = self.calc_lexical_markers(tokens)
        robotic_phrases = self.check_robotic_patterns(clean_text)

        logit = -1.0
        reasons = []

        # 1. AI Lexical Marker Density
        if ai_hits:
            density_boost = (ai_weight / math.sqrt(len(tokens))) * 3.6
            logit += density_boost
            reasons.append(f"AI academic/rhetorical markers detected: {list(set(ai_hits))}")

        if human_hits:
            human_discount = (human_weight / math.sqrt(len(tokens))) * 3.0
            logit -= human_discount
            reasons.append(f"Colloquial human phrasing detected: {list(set(human_hits))}")

        if robotic_phrases:
            logit += len(robotic_phrases) * 1.5
            reasons.append(f"Typical LLM canned phrases detected: {robotic_phrases}")

        # 2. Burstiness / Rhythm Evaluation
        if len(sentences) >= 2:
            if burstiness < 0.35 and len(sentences) >= 3:
                logit += 1.2
                reasons.append(f"Uniform sentence cadence (CV: {burstiness:.2f})")
            elif burstiness > 0.60:
                logit -= 1.3
                reasons.append(f"High human rhythm variance (CV: {burstiness:.2f})")

        # 3. Formal Type-Token Ratio (Vocabulary Variety)
        if 0.60 <= ttr <= 0.80 and len(tokens) > 50:
            logit += 0.8
            reasons.append(f"Controlled lexical dispersion ratio ({ttr:.2f})")

        # 4. Check sentence opener monotony (e.g. over 40% starting with 'The' or 'In')
        if len(sentences) >= 4:
            starters = [s.split()[0].lower() for s in sentences if s.split()]
            if starters:
                top_starter, count = statistics.multimode(starters)[0], max(starters.count(s) for s in starters)
                starter_ratio = count / len(starters)
                if starter_ratio > 0.35 and top_starter in ("the", "in", "it", "this"):
                    logit += 0.7
                    reasons.append(f"Monotonous sentence openers ({top_starter.title()}: {int(starter_ratio*100)}%)")

        # Convert logit to calibrated score [0 - 100]
        final_probability = 1.0 / (1.0 + math.exp(-logit))
        final_score = int(round(final_probability * 100))

        if final_score >= 65:
            verdict = "LIKELY AI-GENERATED"
        elif final_score >= 40:
            verdict = "INCONCLUSIVE / MIXED"
        else:
            verdict = "LIKELY HUMAN-WRITTEN"

        return {
            "ai_score": final_score,
            "verdict": verdict,
            "reasons": reasons,
            "metrics": {
                "burstiness_cv": round(burstiness, 4),
                "sentence_stddev": round(sent_std, 2),
                "type_token_ratio": round(ttr, 4),
                "ai_markers_found": list(set(ai_hits)),
                "human_markers_found": list(set(human_hits)),
                "robotic_phrases_found": robotic_phrases,
                "sentence_count": len(sentences),
                "word_count": len(tokens)
            }
        }
