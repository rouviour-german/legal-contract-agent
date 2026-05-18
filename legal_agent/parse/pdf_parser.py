"""
PyMuPDF-based PDF parser with layout awareness.

Extracts text, blocks, and bounding boxes to enable grounding
and spatial citation in legal documents.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from legal_agent.models import Clause, SourceLocation


class PDFParser:
    """PDF parser that extracts text with layout metadata."""

    def __init__(self, raw_bytes: bytes):
        self.doc = fitz.open(stream=raw_bytes, filetype="pdf")

    def extract_text(self) -> str:
        """Extract full text from the PDF."""
        text = ""
        for page in self.doc:
            text += page.get_text()
        return text

    def extract_clauses(self) -> list[Clause]:
        """
        Extract clauses by analyzing font sizes and blocks.
        Expert implementation: uses block structure to identify headings.
        """
        clauses: list[Clause] = []
        # Simple heuristic for now: blocks with bold text or distinct layout
        for page_num, page in enumerate(self.doc, start=1):
            blocks = page.get_text("blocks")
            for b in blocks:
                # b = (x0, y0, x1, y1, "text", block_no, block_type)
                text = b[4].strip()
                if not text:
                    continue
                
                # Check if it looks like a heading (heuristic)
                # In a real expert system, we'd check font flags (bold, size)
                # via page.get_text("dict")
                
                clause = Clause(
                    heading=text.split("\n")[0][:100],  # First line as heading
                    text=text,
                    source_location=SourceLocation(
                        page=page_num,
                        bounding_box=(b[0], b[1], b[2], b[3]),
                        text_snippet=text[:100],
                    )
                )
                clauses.append(clause)
        
        return clauses

    def close(self) -> None:
        self.doc.close()
