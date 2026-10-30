"""Regulatory document chunking and boundary preservation.

Implements Playbook Section 3b, 4, and Prompt P2:
- Chunks by statutory section/clause/rule boundaries.
- Preserves explicit section numbers and sub-clauses in section_ref.
- Never splits a numbered paragraph mid-sentence.
- Attaches provenance metadata to every chunk.
"""

import re
from uuid import uuid4

from app.rag.schemas import RegChunk, RegDocument

SECTION_PATTERN = re.compile(
    r"(?m)^\s*(?:Section|Rule|Clause|Article|Paragraph)\s+([0-9A-Za-z\.\-]+[^\n]*)"
)


class GuidelineChunker:
    """Splits regulatory texts into legally meaningful chunks preserving section headings."""

    def __init__(
        self,
        target_chunk_chars: int = 1500,
        min_chunk_chars: int = 40,
        index_version: str = "idx_v1_2026_10",
    ):
        self.target_chunk_chars = target_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.index_version = index_version

    def chunk_document(self, document: RegDocument, text: str) -> list[RegChunk]:
        """Split document text into section chunks with complete provenance metadata."""
        cleaned_text = self._clean_text(text)
        raw_sections = self._split_by_sections(cleaned_text)

        chunks: list[RegChunk] = []
        for sec_ref, sec_text in raw_sections:
            if len(sec_text.strip()) < self.min_chunk_chars:
                continue

            # If section is excessively long, split by paragraph boundaries
            sub_chunks = self._split_long_section(sec_text, self.target_chunk_chars)
            for idx, sub_text in enumerate(sub_chunks):
                ref_label = f"{sec_ref} (Part {idx + 1})" if len(sub_chunks) > 1 else sec_ref
                chunk = RegChunk(
                    chunk_id=str(uuid4()),
                    doc_id=document.doc_id,
                    source_name=document.source_name,
                    authority=document.authority,
                    section_ref=ref_label,
                    page_ref=None,
                    text=sub_text.strip(),
                    scope=document.scope,
                    state_code=document.state_code,
                    effective_from=document.effective_from,
                    effective_to=document.effective_to,
                    version_or_date=document.version_or_date,
                    approved=document.approved,
                    license_scope=document.license_scope,
                    index_version=self.index_version,
                )
                chunks.append(chunk)

        return chunks

    def _clean_text(self, text: str) -> str:
        """Strip boilerplate headers, footers, and redundant line-breaks."""
        # Remove common page header/footer lines (e.g. Page 1 of 50, Gazette of India)
        t = re.sub(r"(?i)Page \d+ of \d+", "", text)
        t = re.sub(r"(?i)\[THE GAZETTE OF INDIA\s*:\s*EXTRAORDINARY\]", "", t)
        t = re.sub(r"\r\n", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        return t.strip()

    def _split_by_sections(self, text: str) -> list[tuple[str, str]]:
        """Identify section markers and partition text."""
        matches = list(SECTION_PATTERN.finditer(text))
        if not matches:
            # Fall back to double-newline paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            return [(f"Section General (Para {i+1})", p) for i, p in enumerate(paragraphs)]

        sections: list[tuple[str, str]] = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            # Extract section reference from first matching group
            raw_ref = match.group(0).strip().split("\n")[0]
            # Clean heading
            clean_ref = re.sub(r"\s+", " ", raw_ref)[:60]
            sec_content = text[start:end].strip()
            sections.append((clean_ref, sec_content))

        return sections

    def _split_long_section(self, section_text: str, max_chars: int) -> list[str]:
        """Split a long section without cutting mid-sentence or mid-clause."""
        if len(section_text) <= max_chars:
            return [section_text]

        paragraphs = section_text.split("\n\n")
        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > max_chars and current:
                chunks.append("\n\n".join(current))
                current = [p]
                current_len = p_len
            else:
                current.append(p)
                current_len += p_len + 2

        if current:
            chunks.append("\n\n".join(current))

        return chunks
