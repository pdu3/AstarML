import os, regex as re
from typing import Dict, Iterable, List
from .common import strip_front_matter, extract_title, separate_code_blocks, normalize_space, tokens, windows

FRONT = re.compile(r"^---\\s*\\n([\\s\\S]*?)\\n---\\s*", re.M)
def parse_front(md: str) -> Dict:
    m = FRONT.match(md)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"')
    return out

def _pack_blog_prose(text: str) -> List[str]:
    t = tokens(text)
    n = len(t)
    if n == 0: return []
    if n < 80: return [" ".join(t)]
    if n <= 180:
        segs = windows(t, max_tokens=140, overlap=20)
        return [" ".join(s) for s in segs]
    segs = windows(t, max_tokens=200, overlap=50)
    return [" ".join(s) for s in segs]

def chunk_blog(md_text: str, rel_path: str) -> Iterable[Dict]:
    meta = parse_front(md_text)
    body = strip_front_matter(md_text)
    title = meta.get("title") or extract_title(body) or os.path.basename(rel_path)
    author = meta.get("author", "")
    date = meta.get("published_date", "")

    prose, codes = separate_code_blocks(body)
    idx = 0
    for pc in _pack_blog_prose(prose):
        if pc.strip():
            yield {
                "id": f"{rel_path}#c{idx}",
                "source": "blogs",
                "text": normalize_space(pc),
                "meta": {"post_title": title, "author": author, "published_date": date, "content_type": "prose"}
            }
            idx += 1
    for code in codes:
        c = normalize_space(code)
        if c:
            yield {
                "id": f"{rel_path}#c{idx}",
                "source": "blogs",
                "text": c,
                "meta": {"post_title": title, "author": author, "published_date": date, "content_type": "code"}
            }
            idx += 1

    if idx == 0:  # fallback
        yield {
            "id": f"{rel_path}#c0",
            "source": "blogs",
            "text": normalize_space(body),
            "meta": {"post_title": title, "author": author, "published_date": date, "content_type": "prose"}
        }
