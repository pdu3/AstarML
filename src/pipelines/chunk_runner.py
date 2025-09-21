# src/pipelines/chunk_runner.py
from pathlib import Path
import json
from typing import List

from src.chunking.doc_chunker import chunk_doc
from src.chunking.blog_chunker import chunk_blog
from src.chunking.forum_chunker import chunk_forum_thread

def _pick_dir(root: Path, *candidates: str) -> Path | None:
    for rel in candidates:
        d = root / rel
        if d.is_dir():
            return d
    return None

def _iter_docs(root: Path):
    d = _pick_dir(root, "data/docs", "docs")
    if not d:
        print("[docs] NOT FOUND under", root)
        return
    files = sorted(d.rglob("*.md")) + sorted(d.rglob("*.MD"))
    print(f"[docs] scanning {d} -> {len(files)} files")
    for p in files:
        yield p, p.read_text(encoding="utf-8")

def _iter_blogs(root: Path):
    d = _pick_dir(root, "data/blogs", "blogs")
    if not d:
        print("[blogs] NOT FOUND under", root)
        return
    files = sorted(d.rglob("*.md")) + sorted(d.rglob("*.MD"))
    print(f"[blogs] scanning {d} -> {len(files)} files")
    for p in files:
        yield p, p.read_text(encoding="utf-8")

def _iter_forums(root: Path):
    for rel in ("data/forums/threads.jsonl", "forums/threads.jsonl"):
        f = root / rel
        if f.is_file():
            lines = f.read_text(encoding="utf-8").splitlines()
            print(f"[forums] using {f} -> {len(lines)} lines")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except Exception as e:
                    print("[forums] bad JSONL line:", e)
            return
    print("[forums] NOT FOUND under", root)

def run_chunk(data_root: str = ".", out_path: str = "artifacts/chunks.jsonl",
              sources: List[str] = None) -> int:
    """
    Build chunks.jsonl from docs/forums/blogs.
    Returns the number of chunks written.
    """
    if sources is None:
        sources = ["docs", "forums", "blogs"]

    root = Path(data_root)
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with outp.open("w", encoding="utf-8") as w:
        if "docs" in sources:
            for p, md in _iter_docs(root):
                rel = str(p.relative_to(root))
                for ch in chunk_doc(md, rel):
                    w.write(json.dumps(ch, ensure_ascii=False) + "\n")
                    total += 1
        if "forums" in sources:
            for thread in _iter_forums(root):
                for ch in chunk_forum_thread(thread):
                    w.write(json.dumps(ch, ensure_ascii=False) + "\n")
                    total += 1
        if "blogs" in sources:
            for p, md in _iter_blogs(root):
                rel = str(p.relative_to(root))
                for ch in chunk_blog(md, rel):
                    w.write(json.dumps(ch, ensure_ascii=False) + "\n")
                    total += 1
    return total
