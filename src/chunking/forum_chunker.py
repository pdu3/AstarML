from typing import Dict, Iterable
from .common import normalize_space

def chunk_forum_thread(thread: Dict) -> Iterable[Dict]:
    tid = thread.get("thread_id")
    title = thread.get("title", "")
    q = thread.get("question", "")
    answers = thread.get("answers", []) or []

    accepted = next((a for a in answers if a.get("accepted")), None)
    if accepted:
        text = f"Q: {q} A: {accepted.get('text','')}"
        yield {
            "id": f"data/forums/{tid}#qa",
            "source": "forums",
            "text": normalize_space(text),
            "meta": {
                "thread_id": tid, "title": title,
                "accepted": True, "upvotes": accepted.get("upvotes", 0),
                "author": accepted.get("author",""), "timestamp": accepted.get("timestamp","")
            }
        }
    else:
        yield {
            "id": f"data/forums/{tid}#q",
            "source": "forums",
            "text": normalize_space(f"Q: {q}"),
            "meta": {"thread_id": tid, "title": title, "accepted": False, "upvotes": 0}
        }

    for a in answers:
        if accepted and a is accepted:  # skip accepted (already merged)
            continue
        yield {
            "id": f"data/forums/{tid}#{a.get('id','ans')}",
            "source": "forums",
            "text": normalize_space(f"Answer: {a.get('text','')}"),
            "meta": {
                "thread_id": tid, "title": title,
                "accepted": bool(a.get("accepted", False)),
                "upvotes": a.get("upvotes", 0),
                "author": a.get("author",""),
                "timestamp": a.get("timestamp","")
            }
        }
