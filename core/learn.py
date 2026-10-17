"""Step 6: the learning loop. Read what the reader did, nudge the topic weights.

  click +0.08   like +0.12   skip -0.15   'less like this' -0.25
  every day without reading a topic: weight x 0.98 (old interests fade)
  a like/click on a topic the reader never chose adds it (exploration pays off)
"""
from collections import defaultdict
from datetime import date

from core import config, db


def _clamp(x):
    return max(0.0, min(1.0, x))


def _phrase(counts):
    names = {"click": "opened", "like": "liked", "skip": "skipped", "less": "asked for less of"}
    return " and ".join(f"{names[a]} {n}" for a, n in counts.items() if a in names and n)


def update_profile(user_id):
    """Apply new events + daily decay. Returns a list of human-readable change notes."""
    user = db.get_user(user_id)
    profile = user["profile"]
    weights = profile.setdefault("weights", {})
    profile.setdefault("initial", dict(weights))  # what the reader told us at sign-up
    today = date.today()

    last = profile.get("last_learn_date")
    days = (today - date.fromisoformat(last)).days if last else 0
    if days > 0:
        for t in list(weights):
            weights[t] = round(weights[t] * config.DAILY_DECAY ** days, 3)

    events = [e for e in db.events_after(user_id, profile.get("last_event_id", 0))]
    arts = db.get_articles_by_ids({e["article_id"] for e in events if e["article_id"]})
    net = defaultdict(float)
    counts = defaultdict(lambda: defaultdict(int))
    for e in events:
        delta = config.SIGNAL_DELTAS.get(e["action"])
        art = arts.get(e["article_id"])
        if delta is None or not art:
            continue
        for i, topic in enumerate(art["topics"][:3]):
            d = delta * (1 if i == 0 else 0.5)  # main topic counts fully, side topics half
            old = weights.get(topic)
            if old is None:
                if d <= 0:
                    continue
                old = config.NEW_TOPIC_START
                counts[topic]["_new"] = 1
            weights[topic] = round(_clamp(old + d), 3)
            net[topic] += d
            if i == 0:  # only the story's main topic is named in the notes
                counts[topic][e["action"]] += 1

    notes = []
    for topic, d in sorted(net.items(), key=lambda kv: -abs(kv[1])):
        if abs(d) < 0.1:
            continue
        what = _phrase(counts[topic])
        if not what:
            continue
        if d > 0:
            verb = "Added" if counts[topic].get("_new") else "Raised"
            notes.append(f"{verb} {topic} because you {what} {topic} stories.")
        else:
            notes.append(f"Lowered {topic} because you {what} {topic} stories.")

    profile["weights"] = {t: w for t, w in weights.items() if w >= 0.05}
    if events:
        profile["last_event_id"] = events[-1]["id"]
    profile["last_learn_date"] = today.isoformat()
    log = [{"date": today.isoformat(), "text": n} for n in notes] + profile.get("changes", [])
    profile["changes"] = log[:20]
    db.update_profile(user_id, profile)
    return notes