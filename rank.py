"""Step 3: score every fresh article for ONE reader, then pick the stories for the paper."""
import math
from collections import Counter
from datetime import datetime

from core import config, db
from core.enrich import jaccard, tokens


def _age_hours(published):
    try:
        return max(0.0, (config.utcnow() - datetime.fromisoformat(published)).total_seconds() / 3600)
    except Exception:
        return 24.0


def rank_for_user(user_id, profile, today):
    weights = profile.get("weights", {})
    skipped = db.user_action_ids(user_id, ["skip", "less"])
    seen = db.seen_ids(user_id, today)
    free_tok = tokens(profile.get("free_text", ""))
    items = []
    for a in db.recent_articles(config.ARTICLE_MAX_AGE_HOURS):
        if a["id"] in skipped or a["id"] in seen:
            continue
        matched = sorted(((weights[t], t) for t in a["topics"] if weights.get(t, 0) > 0), reverse=True)
        if matched:
            rel = min(1.0, matched[0][0] + 0.05 * (len(matched) - 1))
            topic = matched[0][1]
        else:
            rel, topic = 0.0, (a["topics"][0] if a["topics"] else "World News")
        fresh = math.exp(-_age_hours(a["published"]) / 24)
        personal = jaccard(free_tok, tokens(f"{a['title']} {a.get('snippet', '')}")) if free_tok else 0.0
        score = 0.50 * rel + 0.22 * a["importance"] + 0.18 * fresh + 0.10 * personal
        if rel >= 0.5:
            why = f"You follow {topic} (interest {int(weights[topic] * 100)}%)."
            if a["importance"] >= 0.6:
                why += " Also covered by several outlets today."
        elif a["importance"] >= 0.6:
            why = "A major story covered by several outlets today."
        else:
            why = f"Fresh {topic} story from {a['source']}."
        if personal >= 0.12:
            why += " It also matches the specifics you described at sign-up."
        items.append({"article": a, "score": score, "rel": rel, "fresh": fresh, "topic": topic,
                      "why": why, "explore": False, "also": [], "_tok": tokens(a["title"])})
    items.sort(key=lambda i: -i["score"])
    return items


def select(items, n):
    """Pick n stories: mostly by score, a share from outside the bubble, one story per event,
    and no source dominating."""
    n_explore = max(1, round(n * config.EXPLORATION_SHARE)) if n >= 6 else 0
    core = [i for i in items if i["rel"] >= config.INTEREST_THRESHOLD]
    explore_pool = sorted((i for i in items if i["rel"] < config.INTEREST_THRESHOLD),
                          key=lambda i: -(0.6 * i["article"]["importance"] + 0.4 * i["fresh"]))
    picked, per_source = [], Counter()

    def add(item, limit):
        if len(picked) >= limit:
            return False
        a = item["article"]
        for p in picked:  # same story from another outlet -> merge, don't repeat
            if jaccard(item["_tok"], p["_tok"]) >= 0.5:
                if a["source"] != p["article"]["source"] and a["source"] not in p["also"]:
                    p["also"].append(a["source"])
                return False
        if per_source[a["source"]] >= config.MAX_PER_SOURCE:
            return False
        picked.append(item)
        per_source[a["source"]] += 1
        return True

    for item in core:
        add(item, n - n_explore)
    seen_topics = set()
    for item in explore_pool:  # first pass: different topics each
        if item["topic"] not in seen_topics and add(item, n):
            item["explore"] = True
            item["why"] = (f"Outside your usual topics: {item['topic']}. "
                           "Included so your paper doesn't become an echo chamber.")
            seen_topics.add(item["topic"])
    for item in items:  # still short? fill with best remaining
        add(item, n)
    return picked