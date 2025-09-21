# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List, Dict, Tuple
from difflib import SequenceMatcher

_word = re.compile(r"[a-z0-9]+")

def _tokset(s: str) -> set:
    return set(_word.findall((s or "").lower().replace("-", " ").replace(".", " ")))

def _sim(a: str, b: str) -> float:
    # Combined similarity: token-level Jaccard as primary, shape similarity as secondary
    ta, tb = _tokset(a), _tokset(b)
    inter, union = len(ta & tb), len(ta | tb) or 1
    jacc = inter / union
    shape = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return 0.7 * jacc + 0.3 * shape

def cluster_keys(keys: List[str], threshold: float = 0.62) -> Dict[int, List[str]]:
    """Simple single-linkage clustering."""
    clusters: List[List[str]] = []
    for k in keys:
        placed = False
        for cl in clusters:
            if any(_sim(k, x) >= threshold for x in cl):
                cl.append(k); placed = True; break
        if not placed:
            clusters.append([k])
    return {i: cl for i, cl in enumerate(clusters)}

# Value normalization: 60s/60 sec/60000ms → unify; on/off/true/false; lowercase enums
def normalize_value(v: str) -> str:
    s = (v or "").strip().lower()
    # Time / granularity
    m = re.match(r"^(\d+)\s*(ms|millisecond[s]?|s|sec|second[s]?)?$", s)
    if m:
        num = m.group(1); unit = (m.group(2) or "s")
        return f"{num}{'ms' if unit.startswith('ms') else 's'}"
    # Boolean
    if s in {"on","true","yes","enabled"}: return "on"
    if s in {"off","false","no","disabled"}: return "off"
    return s

def value_type(v: str) -> str:
    if re.fullmatch(r"\d+(\.\d+)?(ms|s)?", v): return "number"  # Values with units are still comparable as numbers
    return "enum"

def value_to_number(v: str) -> float | None:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(ms|s)?", v)
    if not m: return None
    x = float(m.group(1)); unit = m.group(2) or "s"
    return x/1000.0 if unit=="ms" else x

def detect_conflicts(items: List[Tuple[str,str,Dict]]) -> Dict:
    """
    items: [(key, val, meta), ...]  meta should contain source and id for printing provenance
    Returns {'consensus': {val: weight, ...}, 'conflicts': [{'val': ..., 'support': [...]} ...]}
    """
    # Normalize values
    norm = [(k, normalize_value(v), meta) for k, v, meta in items]
    vals = {}
    for _, v, meta in norm:
        vals.setdefault(v, []).append(meta)
    if len(vals) <= 1:
        # Only one value ⇒ no conflict
        return {"consensus": {list(vals.keys())[0]: len(list(vals.values())[0])}, "conflicts": []}

    # Numeric type: if different numbers (beyond eps) ⇒ conflict
    typs = {value_type(v) for v in vals.keys()}
    conflicts = []
    if typs == {"number"}:
        nums = {v: value_to_number(v) for v in vals}
        # Simple approach: group by distinct numeric values
        for v, metas in vals.items():
            conflicts.append({"val": v, "support": metas})
        return {"consensus": {}, "conflicts": conflicts}
    else:
        # Enum/Boolean: different enums are treated as conflicts directly
        for v, metas in vals.items():
            conflicts.append({"val": v, "support": metas})
        return {"consensus": {}, "conflicts": conflicts}
