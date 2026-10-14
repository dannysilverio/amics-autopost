#!/usr/bin/env python3
"""Auto-approval gate. Danny's standing rule (Oct 14 2026): organic posts may go out
automatically as long as they are informative and within what Amics does. Anything that
fails stays held for Danny. Organic posts only: never ads, boosts, or paid promotion."""
import json, re, sys

TOPICS = {"advertising", "marketing", "paid media", "programmatic", "ai", "creative", "design", "measurement", "tracking"}
BLOCK = [
    r"\bguarantee[sd]?\b", r"\bbook (now|a call|today)\b", r"\b(dm|call|text|email) (us|me)\b",
    r"\bfree (consult|audit|quote|trial)\b", r"\blimited time\b", r"\bsign up\b", r"\bdiscount\b",
    r"\$\s?\d", r"\b\d+\s?%\b", r"\b(10|[2-9])x\b", r"\bcure[sd]?\b", r"\bdiagnos", r"\blegal advice\b",
    r"\bwe (will|can) (get|make) you\b", r"\bour (client|clients) (made|saw|got)\b",
]
MAX_CAPTION = 2200

def check(item):
    why = []
    text = (item.get("caption", "") + " " + item.get("script", "")).lower()
    if item.get("topic", "").lower() not in TOPICS: why.append("topic not in allowed list")
    for p in BLOCK:
        if re.search(p, text): why.append(f"blocked pattern: {p}")
    if "—" in text or "–" in text: why.append("contains em or en dash")
    if len(item.get("caption", "")) > MAX_CAPTION: why.append("caption too long")
    if item.get("type") == "reel" and not str(item.get("video_url", "")).startswith("https://"): why.append("no public video url")
    if item.get("type") == "carousel" and not item.get("image_urls"): why.append("no images")
    if item.get("is_ad"): why.append("ads are never auto-approved")
    return why

def main():
    sched = json.load(open("schedule.json")); held = 0
    for it in sched["items"]:
        if it.get("posted_at"): continue
        if it.get("hold"):  # Danny's manual hold always wins
            it["approved"] = False; held += 1; continue
        why = check(it)
        it["approved"] = not why
        it["approval_note"] = "auto-gate passed" if not why else "; ".join(why)
        held += bool(why)
    json.dump(sched, open("schedule.json", "w"), indent=2)
    print(f"{len(sched['items'])} items, {held} held")
    for it in sched["items"]:
        if not it.get("approved") and not it.get("posted_at"): print(" HELD", it["id"], "->", it.get("approval_note", "manual hold"))

if __name__ == "__main__":
    main()
