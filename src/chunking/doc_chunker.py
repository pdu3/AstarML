# src/chunking/doc_chunker.py
import os
from typing import Dict, List, Iterable
from .common import (
    strip_front_matter, extract_title,
    split_by_h2_h3, separate_code_blocks,
    normalize_space, tokens, windows
)

# Tunables
TARGET, MINLEN, MAXLEN, OVERLAP = 280, 120, 380, 70

def _pack_prose(text: str) -> List[str]:
    """Pack prose into token windows with overlap. Never return an empty list if text has tokens."""
    toks = tokens(text)
    n = len(toks)
    if n == 0:
        return []
    # keep small sections whole (avoid over-fragmentation)
    if n < MINLEN or n <= TARGET + 40:
        return [" ".join(toks)]
    segs = windows(toks, max_tokens=min(MAXLEN, TARGET), overlap=OVERLAP)
    return [" ".join(s) for s in segs]

def chunk_doc(md_text: str, rel_path: str) -> Iterable[Dict]:
    """
    Yield doc chunks as dictionaries with stable IDs.
    This function is defensive: even with odd markdown it should still emit chunks.
    """
    # ---- 0) Preprocess
    body = strip_front_matter(md_text) or md_text  # if regex misses, fall back to raw text
    title = extract_title(body) or os.path.basename(rel_path)

    # ---- 1) Structure-first split (H2/H3). If nothing detected, use full body.
    sections = list(split_by_h2_h3(body))
    if not sections:
        sections = [ ([], body) ]

    produced = 0
    idx = 0

    for section_path, section_text in sections:
        # Separate fenced code blocks from prose
        prose, codes = separate_code_blocks(section_text)

        # ---- 2) Prose chunks
        prose_chunks = _pack_prose(prose)
        for pc in prose_chunks:
            text = normalize_space(pc)
            if not text:
                continue
            yield {
                "id": f"{rel_path}#c{idx}",
                "source": "docs",
                "text": text,
                "meta": {
                    "doc_title": title,
                    "section_path": section_path,
                    "version": "v2.1",
                    "content_type": "prose"
                }
            }
            idx += 1
            produced += 1

        # ---- 3) Code chunks (kept verbatim but space-normalized)
        for code in codes:
            c = normalize_space(code)
            if not c:
                continue
            yield {
                "id": f"{rel_path}#c{idx}",
                "source": "docs",
                "text": c,
                "meta": {
                    "doc_title": title,
                    "section_path": section_path,
                    "version": "v2.1",
                    "content_type": "code"
                }
            }
            idx += 1
            produced += 1

    # ---- 4) Last-resort fallback: if nothing was produced, emit the whole body once
    if produced == 0:
        text = normalize_space(body)
        if text:
            yield {
                "id": f"{rel_path}#c0",
                "source": "docs",
                "text": text,
                "meta": {
                    "doc_title": title,
                    "section_path": [],
                    "version": "v2.1",
                    "content_type": "prose"
                }
            }

# import os
# from typing import Dict, List, Iterable
# from .common import strip_front_matter, extract_title, split_by_h2_h3, separate_code_blocks, normalize_space, tokens, windows
#
# TARGET, MINLEN, MAXLEN, OVERLAP = 280, 120, 380, 70
#
# def _pack_prose(text: str) -> List[str]:
#     toks = tokens(text)
#     n = len(toks)
#     if n == 0:
#         return []
#     if n < MINLEN or n <= TARGET + 40:
#         return [" ".join(toks)]
#     segs = windows(toks, max_tokens=min(MAXLEN, TARGET), overlap=OVERLAP)
#     return [" ".join(s) for s in segs]
#
# def chunk_doc(md_text: str, rel_path: str) -> Iterable[Dict]:
#     body = strip_front_matter(md_text)
#     title = extract_title(body) or os.path.basename(rel_path)
#     sections = list(split_by_h2_h3(body))
#     idx = 0
#     for section_path, section_text in sections:
#         prose, codes = separate_code_blocks(section_text)
#         for pc in _pack_prose(prose):
#             if pc.strip():
#                 yield {
#                     "id": f"{rel_path}#c{idx}",
#                     "source": "docs",
#                     "text": normalize_space(pc),
#                     "meta": {"doc_title": title, "section_path": section_path, "version": "v2.1"}
#                 }
#                 idx += 1
#         for code in codes:
#             c = normalize_space(code)
#             if c:
#                 yield {
#                     "id": f"{rel_path}#c{idx}",
#                     "source": "docs",
#                     "text": c,
#                     "meta": {"doc_title": title, "section_path": section_path, "version": "v2.1", "content_type": "code"}
#                 }
#                 idx += 1
