import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SentenceChunk:
    id: str
    text: str
    paragraph_id: int
    index_in_para: int
    word_count: int
    char_start: int
    char_end: int


@dataclass
class ParagraphChunk:
    id: int
    text: str
    sentences: List[SentenceChunk] = field(default_factory=list)
    word_count: int = 0


@dataclass
class DocumentStructure:
    raw_text: str
    cleaned_text: str
    paragraphs: List[ParagraphChunk]
    all_sentences: List[SentenceChunk]
    total_words: int
    total_paragraphs: int
    total_sentences: int


class DocumentChunker:
    """Robust hierarchical chunker for processing entire documents of arbitrary length.

    Preserves paragraph structure, sentence offsets, and allows seamless re-assembly.
    """

    def __init__(self, min_sentence_words: int = 2):
        self.min_sentence_words = min_sentence_words

    def split_sentences(self, paragraph_text: str) -> List[str]:
        """Splits paragraph into sentences while handling abbreviations, initials,

        and missing spaces after periods.
        """
        if not paragraph_text.strip():
            return []

        # Fix missing space after periods between lowercase and uppercase letter (e.g. 'reality.This')
        normalized = re.sub(r'([a-z0-9])\.([A-Z])', r'\1. \2', paragraph_text)

        # Protect common abbreviations: e.g., i.e., Dr., Mr., etc.
        abbreviations = ["e.g.", "i.e.", "dr.", "mr.", "mrs.", "ms.", "prof.", "vs.", "etc.", "fig.", "al."]
        for abbr in abbreviations:
            escaped = abbr.replace(".", r"\.")
            def repl_abbr(match):
                return match.group(0).replace(".", "§DOT§")
            normalized = re.sub(rf'\b{escaped}', repl_abbr, normalized, flags=re.IGNORECASE)

        # Split on sentence terminals followed by whitespace or quotes
        raw_parts = re.split(r'(?<=[.!?])(?=[\s"\'\n]+|$)', normalized)

        sentences = []
        for part in raw_parts:
            s = part.replace("§DOT§", ".").strip()
            if s and len(s.split()) >= self.min_sentence_words:
                sentences.append(s)

        return sentences

    def parse_document(self, text: str) -> DocumentStructure:
        """Parses a full document into structured paragraphs and sentences."""
        if not text:
            return DocumentStructure(
                raw_text="",
                cleaned_text="",
                paragraphs=[],
                all_sentences=[],
                total_words=0,
                total_paragraphs=0,
                total_sentences=0,
            )

        # Split into paragraphs by double newlines or newline blocks
        raw_paras = re.split(r'\n\s*\n', text.strip())
        paragraphs: List[ParagraphChunk] = []
        all_sentences: List[SentenceChunk] = []

        total_word_counter = 0
        global_sent_id = 0

        current_char_offset = 0

        for p_idx, p_text in enumerate(raw_paras):
            clean_p = p_text.strip()
            if not clean_p:
                continue

            sent_texts = self.split_sentences(clean_p)
            p_sentences: List[SentenceChunk] = []
            p_words = 0

            for s_idx, s_text in enumerate(sent_texts):
                words = s_text.split()
                w_count = len(words)
                p_words += w_count
                total_word_counter += w_count

                # Estimate character offsets
                start_offset = text.find(s_text, current_char_offset)
                if start_offset == -1:
                    start_offset = current_char_offset
                end_offset = start_offset + len(s_text)
                current_char_offset = end_offset

                chunk = SentenceChunk(
                    id=f"p{p_idx}_s{s_idx}",
                    text=s_text,
                    paragraph_id=p_idx,
                    index_in_para=s_idx,
                    word_count=w_count,
                    char_start=start_offset,
                    char_end=end_offset
                )
                p_sentences.append(chunk)
                all_sentences.append(chunk)
                global_sent_id += 1

            p_chunk = ParagraphChunk(
                id=p_idx,
                text=clean_p,
                sentences=p_sentences,
                word_count=p_words
            )
            paragraphs.append(p_chunk)

        return DocumentStructure(
            raw_text=text,
            cleaned_text="\n\n".join(p.text for p in paragraphs),
            paragraphs=paragraphs,
            all_sentences=all_sentences,
            total_words=total_word_counter,
            total_paragraphs=len(paragraphs),
            total_sentences=len(all_sentences)
        )

    def reassemble(self, paragraphs_with_rectified_sentences: List[List[str]]) -> str:
        """Reassembles rectified sentences back into a coherent multi-paragraph document."""
        paragraph_texts = []
        for sent_list in paragraphs_with_rectified_sentences:
            para = " ".join(s.strip() for s in sent_list if s.strip())
            if para:
                paragraph_texts.append(para)
        return "\n\n".join(paragraph_texts)
