"""Step 4: turn the ranked stories into ONE edition (a JSON dict).
The web page and the PDF both draw from this same dict, so they always match.
Personalization drives layout here: lead story, section order and size, summary length."""
import json
import re
from collections import defaultdict
from datetime import date as date_cls, datetime
from urllib.parse import urlparse

from core import config, db, rank


def _first_sentence(text):
    return re.split(r"(?<=[.!?])\s+", (text or "").strip())[0]


def _fit(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def _ago(published):
    try:
        hours = (config.utcnow() - datetime.fromisoformat(published)).total_seconds() / 3600
    except Exception:
        return ""
    return f"{int(hours)}h ago" if hours < 24 else f"{int(hours // 24)}d ago"


def _story(item, limit):
    a = item["article"]
    return {
        "id": a["id"], "title": a["title"], "url": a["url"], "source": a["source"],
        "domain": urlparse(a["url"]).netloc.replace("www.", ""),
        "published_label": _ago(a["published"]), "summary": _fit(a["summary"], limit),
        "image": a["image"], "topic": item["topic"], "reading_min": a["reading_min"],
        "why": item["why"], "also": item["also"], "explore": item["explore"],
    }


def edition_paths(user_id, date):
    return (config.EDITIONS_DIR / f"{user_id}_{date}.json",
            config.EDITIONS_DIR / f"{user_id}_{date}.pdf")


def load_edition(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def build_edition(user_id, date=None, rebuild=False):
    """Return today's edition for this reader (building it if needed). None if no articles."""
    user = db.get_user(user_id)
    date = date or date_cls.today().isoformat()
    json_path, pdf_path = edition_paths(user_id, date)
    row = db.get_edition_row(user_id, date)
    if row and not rebuild and json_path.exists():
        return load_edition(json_path)

    profile = user["profile"]
    weights = profile.get("weights", {})
    style = user["style"] if user["style"] in config.STYLE_SUMMARY_CHARS else "balanced"
    n = config.STORIES_BY_MINUTES.get(user["reading_time"], 14)
    n = max(6, round(n * config.STYLE_COUNT_FACTOR[style]))
    limit = config.STYLE_SUMMARY_CHARS[style]

    picked = rank.select(rank.rank_for_user(user_id, profile, date), n)
    main = [i for i in picked if not i["explore"]]
    explore = [i for i in picked if i["explore"]]
    if not main:
        main, explore = picked, []
    if not main:
        return None

    lead = _story(main[0], int(limit * 1.5))
    secondary = [_story(i, limit) for i in main[1:4]]

    groups = defaultdict(list)
    for item in main[4:]:
        groups[item["topic"]].append(item)
    order = sorted(groups, key=lambda t: (-weights.get(t, 0), -len(groups[t])))
    sections, briefs = [], []
    for topic in order:
        w = weights.get(topic, 0)
        size = "large" if w >= 0.7 else "medium" if w >= 0.4 else "small"
        cap = {"large": 5, "medium": 3, "small": 2}[size]
        items = groups[topic]
        sections.append({"name": topic, "size": size, "weight": round(w, 2),
                         "stories": [_story(i, limit) for i in items[:cap]]})
        briefs += [_story(i, 0) for i in items[cap:]]
    if explore:
        sections.append({"name": "Beyond Your Bubble", "size": "medium", "weight": 0, "explore": True,
                         "stories": [_story(i, limit) for i in explore]})

    seen_topics, three = set(), []
    for item in main:
        if item["topic"] not in seen_topics and len(three) < 3:
            seen_topics.add(item["topic"])
            three.append({"id": item["article"]["id"], "headline": item["article"]["title"],
                          "takeaway": _first_sentence(item["article"]["summary"])})

    all_stories = [lead] + secondary + [s for sec in sections for s in sec["stories"]]
    top = sorted(weights.items(), key=lambda kv: -kv[1])[:4]
    d = datetime.strptime(date, "%Y-%m-%d")
    edition = {
        "user_id": user_id, "reader": user["name"], "date": date,
        "date_long": f"{d:%A}, {d.day} {d:%B %Y}",
        "edition_no": row["edition_no"] if row else db.count_editions(user_id) + 1,
        "reading_time": user["reading_time"], "style": style,
        "interests_line": ", ".join(t for t, _ in top) or "general news",
        "lead": lead, "secondary": secondary, "sections": sections, "briefs": briefs,
        "three_things": three,
        "editor_note": (
            f"Good morning. We led with {lead['topic']} because it scored highest "
            f"against how you actually read, not just the topics you picked on day one."
        ),
        "learning_note": [c["text"] for c in profile.get("changes", [])[:3]],
        "stats": {"stories": len(all_stories) + len(briefs),
                  "sources": len({s["source"] for s in all_stories + briefs}),
                  "est_minutes": sum(s["reading_min"] for s in all_stories)},
        "generated_at": config.utcnow().isoformat(timespec="seconds"),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(edition, f, ensure_ascii=False, indent=2)
    if pdf_path.exists():
        pdf_path.unlink()  # stale PDF: it will be re-rendered from the new edition
    db.save_edition(user_id, date, edition["edition_no"], json_path)
    db.record_shown(user_id, [s["id"] for s in all_stories + briefs], date)
    return edition