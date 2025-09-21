# Edge weight from evidence to claim: fusion score / source weight / freshness (no LLM)
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime
from dateutil import parser as dtparser

SOURCE_WEIGHT = {"docs": 1.0, "forums": 0.88, "blogs": 0.75}

def _freshness(ts: str | None) -> float:
    """Temporal freshness (0–1): newer → closer to 1; None returns 0.5."""
    if not ts: return 0.5
    try:
        t = dtparser.parse(ts)
    except Exception:
        return 0.5
    days = max(0, (datetime.utcnow() - t).days)
    # Decays to ~0 after 180 days; within ~7 days it's close to 1
    if days >= 180: return 0.0
    return max(0.0, 1.0 - days / 180.0)

def evidence_weight(meta: Dict[str, Any], base_score: float) -> float:
    """
    Composite weight (~0–1 range, not strictly enforced):
    w = 0.6 * fused_norm + 0.3 * src_norm + 0.1 * freshness
    - base_score: score from the fusion stage (e.g., QueryFusion's relative_score)
    - If meta["_fused_raw"] exists, prefer that value
    """
    fused = float(meta.get("_fused_raw", base_score or 0.0))
    # Simple normalization (stable enough; for strict normalization, do it in the pipeline)
    fused_norm = 1.0 / (1.0 + pow(2.71828, -fused))  # sigmoid

    src = (meta.get("source") or "docs").lower()
    sw  = SOURCE_WEIGHT.get(src, 1.0)
    # Normalize to 0–1
    sw_norm = (sw - min(SOURCE_WEIGHT.values())) / (max(SOURCE_WEIGHT.values()) - min(SOURCE_WEIGHT.values()) or 1.0)

    fresh = _freshness(meta.get("time") or meta.get("timestamp"))

    return 0.6 * fused_norm + 0.3 * sw_norm + 0.1 * fresh
