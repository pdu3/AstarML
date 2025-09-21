# src/graphrag/extract_llm_open.py
import os, json
from typing import List, Dict
from openai import OpenAI

SYS = "You extract config-like claims. Return JSON only."

USR = """Extract configuration-style claims from the text.

Rules:
- Propose concise keys (e.g., param.batch_size, timeout, retries, lr_scheduler, concurrency, artifact_retention_days, metrics.granularity, etc.).
- Values must be short: numbers/units/enums/booleans (examples: 32, 60s, 60000ms, cosine, step, on/off, true/false, 1/2).
- Each item MUST include a short sentence span from the text.
- If nothing matches, return empty list.
- Output JSON ONLY in this exact shape:
  {{ "claims": [ {{ "key":"...", "val":"...", "sent":"..." }} ] }}

Text:
<<<
{chunk}
>>>"""

def _client():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)

def extract_claims_llm_open(text: str, model: str = None) -> List[Dict]:
    if not text or not text.strip():
        return []
    model = model or os.getenv("EXTRACT_LLM_MODEL", "gpt-4o-mini")

    user_content = USR.replace("{chunk}", text)
    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYS},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except Exception:
        import re
        m = re.search(r"\{.*\}", content, re.S)
        data = json.loads(m.group(0)) if m else {}

    out = []
    for c in (data.get("claims") or []):
        k = (c.get("key") or "").strip()
        v = (c.get("val") or "").strip()
        s = (c.get("sent") or "").strip()
        if k and v and s:
            out.append({"key": k, "val": v, "sent": s})
    return out
