"""Step 2: understand each article - topics, short summary, reading time, importance.
Works with keyword rules alone; if ANTHROPIC_API_KEY is set, Claude writes the
tags and a fresh 2-sentence summary instead (better quality, and in our own words)."""
import json
import re

from core import config, db

STOP = set("""the and for with from that this after over into than says will has have had not but about
more your their they them been were what when where which while also just only like some such""".split())


def tokens(text):
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 3 and w not in STOP}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


# ---------- rule-based tagging ----------
def tag_topics(title, snippet, hint=None):
    text = f"{title} {snippet}".lower()
    hits = []
    for topic, words in config.TOPIC_KEYWORDS.items():
        n = sum(1 for w in words if re.search(r"\b" + re.escape(w) + r"\b", text))
        if n:
            hits.append((n, topic))
    hits.sort(key=lambda h: -h[0])
    topics = [t for _, t in hits[:3]]
    if hint and hint not in topics:
        if topics:
            topics.append(hint)
        else:
            topics.insert(0, hint)
    return topics or ["World News"]


def make_summary(snippet, title, max_chars=300):
    text = (snippet or "").strip() or title
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for s in sentences[:2]:
        if len(out) + len(s) > max_chars:
            break
        out = f"{out} {s}".strip()
    return out or text[:max_chars].rsplit(" ", 1)[0] + "…"


def reading_minutes(snippet):
    return max(1, min(5, round(len(snippet or "") / 400) + 1))


# ---------- optional LLM tagging ----------
def _llm_enrich(article):
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        prompt = (
            "You are a newspaper sub-editor. Given an article headline and snippet, reply with ONLY "
            'JSON: {"topics": [up to 3 from this list: ' + ", ".join(config.TOPICS) + '], '
            '"summary": "two plain sentences in your own words, no quotes"}.\n\n'
            f"Headline: {article['title']}\nSnippet: {article['snippet']}"
        )
        msg = client.messages.create(model=config.LLM_MODEL, max_tokens=300,
                                     messages=[{"role": "user", "content": prompt}])
        data = json.loads(re.search(r"\{.*\}", msg.content[0].text, re.S).group(0))
        topics = [t for t in data.get("topics", []) if t in config.TOPICS]
        summary = str(data.get("summary", "")).strip()
        return (topics, summary) if topics and summary else None
    except Exception:
        return None


# ---------- importance ----------
def compute_importance():
    """An article is 'bigger news' when several outlets cover the same story."""
    arts = db.recent_articles(config.ARTICLE_MAX_AGE_HOURS)
    toks = [tokens(a["title"]) for a in arts]
    for i, a in enumerate(arts):
        outlets = {b["source"] for j, b in enumerate(arts)
                   if i != j and b["source"] != a["source"] and jaccard(toks[i], toks[j]) >= 0.3}
        db.set_importance(a["id"], round(0.25 + 0.75 * min(1.0, len(outlets) / 2), 2))


def run():
    """Enrich all new articles, then refresh importance. Returns number enriched."""
    pending = db.get_unenriched()
    llm_used = 0
    for a in pending:
        result = None
        if llm_used < config.LLM_MAX_PER_RUN:
            result = _llm_enrich(a)
            llm_used += 1 if config.ANTHROPIC_API_KEY else 0
        topics, summary = result if result else (
            tag_topics(a["title"], a["snippet"], a.get("hint_topic")),
            make_summary(a["snippet"], a["title"]))
        db.save_enrichment(a["id"], topics, summary, reading_minutes(a["snippet"]))
    compute_importance()
    return len(pending)