"""Chunk a document by section, not by a fixed character count (README §2.2).

Boundaries: blank lines, ALL-CAPS titles (invoice/report headers), numbered
sections ("Article N –", "N. Title" — see generate_docs.py), and a few
invoice-specific anchors ("Facturé à"). A max-length safety valve avoids a
pathologically large single chunk when a document has no structure at all —
it's a fallback, not the primary splitting rule.
"""
import re

MAX_CHUNK_CHARS = 800

NUMBERED_SECTION_RE = re.compile(r"^(Article \d+\s*[–-]|\d+\.\s)")
INVOICE_ANCHORS = {"Facturé à"}


def _is_section_boundary(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.isupper() and len(stripped) > 3:
        return True
    if NUMBERED_SECTION_RE.match(stripped):
        return True
    if stripped in INVOICE_ANCHORS:
        return True
    return False


def _hard_split(s: str, max_len: int) -> list[str]:
    """Fallback for a single chunk that's still too long (e.g. one huge line
    with no internal structure at all) — plain character-count slicing."""
    return [s[i:i + max_len] for i in range(0, len(s), max_len)]


def chunk_by_section(text: str, max_chunk_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    chunks = []
    current: list[str] = []

    def flush():
        if not current:
            return
        joined = "\n".join(current).strip()
        current.clear()
        if not joined:
            return
        if len(joined) > max_chunk_chars:
            chunks.extend(_hard_split(joined, max_chunk_chars))
        else:
            chunks.append(joined)

    for line in text.split("\n"):
        if _is_section_boundary(line) and current:
            flush()
        if line.strip():
            current.append(line)
        if current and sum(len(l) for l in current) > max_chunk_chars:
            flush()
    flush()
    return chunks
