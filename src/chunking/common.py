import regex as re
from typing import List, Tuple, Iterable, Optional

FRONT_MATTER_RE = re.compile(r"^---[\\s\\S]*?---\\s*", re.M)
HEADING_RE = re.compile(r"^(#{1,6})\\s+(.*)$", re.M)
FENCED_CODE_RE = re.compile(r"```[\\s\\S]*?```", re.M)

def strip_front_matter(md: str) -> str:
    return FRONT_MATTER_RE.sub("", md, count=1)

def extract_title(md: str) -> Optional[str]:
    m = re.search(r"^#\\s+(.*)$", md, flags=re.M)
    return m.group(1).strip() if m else None

def split_by_h2_h3(md: str) -> Iterable[Tuple[List[str], str]]:
    """Yield (section_path, section_text) split on H2/H3."""
    lines = md.strip().splitlines()
    sections, path, buf, cur_level = [], [], [], None

    def flush():
        if buf:
            sections.append((path.copy(), "\n".join(buf).strip()))

    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if 2 <= level <= 3:
                flush()
                # rebuild path based on level (H2 -> depth 1, H3 -> depth 2)
                while len(path) >= (level - 1):
                    path.pop()
                while len(path) < (level - 2):
                    path.append("")
                path.append(title)
                cur_level = level
                buf = []
                continue
        buf.append(line)
    flush()
    return sections or [([], md)]

def separate_code_blocks(md: str):
    codes = FENCED_CODE_RE.findall(md)
    prose = FENCED_CODE_RE.sub("", md).strip()
    return prose, codes

def normalize_space(s: str) -> str:
    return re.sub(r"\\s+", " ", s).strip()

def tokens(text: str) -> List[str]:
    return re.findall(r"\\w+|\\S", text)

def windows(tok: List[str], max_tokens: int, overlap: int):
    if len(tok) <= max_tokens:
        return [tok]
    out, i = [], 0
    while i < len(tok):
        j = min(len(tok), i + max_tokens)
        out.append(tok[i:j])
        if j == len(tok):
            break
        i = max(0, j - overlap)
    return out
