"""Central settings: paths, topics, feeds, ranking and learning constants."""
import os
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EDITIONS_DIR = DATA_DIR / "editions"
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = DATA_DIR / "paper.db"
for _d in (DATA_DIR, EDITIONS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def utcnow():
    """Naive UTC 'now' (all stored timestamps are naive UTC ISO strings)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---- Optional LLM (the app works without it, using keyword rules) ----
def _load_env():
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


_load_env()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("PAPER_LLM_MODEL", "claude-haiku-5-5")
LLM_MAX_PER_RUN = 40

# ---- Topics (must match the chips in pages/1_Onboarding.py) ----
TOPICS = [
    "AI & Tech", "Cricket", "Football", "Business", "Startups", "Pakistan Politics",
    "World News", "Climate", "Health", "Science", "Education", "Culture & Film",
    "Finance & Markets", "Formula 1",
]

TOPIC_KEYWORDS = {
    "AI & Tech": ["ai", "artificial intelligence", "chatbot", "llm", "machine learning", "software",
                  "smartphone", "cyber", "chip", "semiconductor", "robot", "tech", "gadget",
                  "iphone", "android", "openai", "nvidia"],
    "Cricket": ["cricket", "test match", "odi", "t20", "psl", "icc", "wicket", "batter",
                "bowler", "pcb", "innings", "test series"],
    "Football": ["football", "premier league", "la liga", "fifa", "champions league",
                 "striker", "goalkeeper"],
    "Business": ["business", "economy", "company", "companies", "earnings", "inflation",
                 "trade", "retail", "tariff", "industry"],
    "Startups": ["startup", "startups", "funding", "venture", "founder", "seed round",
                 "series a", "unicorn"],
    "Pakistan Politics": ["pakistan", "islamabad", "lahore", "karachi", "pti", "pml-n", "ppp",
                          "national assembly", "senate", "supreme court", "imran khan",
                          "parliament", "election", "minister", "opposition"],
    "World News": ["war", "ceasefire", "united nations", "president", "israel", "gaza",
                   "ukraine", "russia", "china", "summit", "diplomat", "sanctions"],
    "Climate": ["climate", "flood", "floods", "heatwave", "emissions", "carbon", "renewable",
                "solar", "wildfire", "global warming", "monsoon"],
    "Health": ["health", "hospital", "disease", "vaccine", "cancer", "diabetes", "nutrition",
               "mental health", "dengue", "medicine", "sleep"],
    "Science": ["science", "scientists", "researchers", "nasa", "space", "physics", "biology",
                "telescope", "quantum", "discovery", "species", "galaxy"],
    "Education": ["education", "university", "students", "school", "exam", "exams",
                  "curriculum", "scholarship", "hec"],
    "Culture & Film": ["film", "movie", "cinema", "actor", "actress", "music", "album",
                       "festival", "drama", "netflix", "bollywood", "novel"],
    "Finance & Markets": ["stock", "stocks", "shares", "market", "markets", "kse", "psx",
                          "rupee", "dollar", "interest rate", "crypto", "bitcoin", "imf",
                          "budget", "currency"],
    "Formula 1": ["formula 1", "f1", "grand prix", "verstappen", "hamilton", "ferrari",
                  "mclaren", "qualifying"],
}

# ---- RSS feeds. TEST EACH URL once; delete any that are dead. ----
# "topic" is the fallback tag when keywords find nothing.
FEEDS = [
    {"name": "Dawn", "url": "https://www.dawn.com/feeds/home", "topic": "Pakistan Politics"},
    {"name": "Dawn", "url": "https://www.dawn.com/feeds/business", "topic": "Business"},
    {"name": "Dawn", "url": "https://www.dawn.com/feeds/sport", "topic": "Cricket"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "topic": "World News"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "topic": "AI & Tech"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/business/rss.xml", "topic": "Business"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "topic": "Science"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/health/rss.xml", "topic": "Health"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/education/rss.xml", "topic": "Education"},
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml", "topic": "Culture & Film"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml", "topic": "Football"},
    {"name": "BBC Sport", "url": "https://feeds.bbci.co.uk/sport/formula1/rss.xml", "topic": "Formula 1"},
    {"name": "ESPNcricinfo", "url": "https://www.espncricinfo.com/rss/content/story/feeds/0.xml", "topic": "Cricket"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "topic": "AI & Tech"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/", "topic": "Startups"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "topic": "World News"},
    {"name": "The Guardian", "url": "https://www.theguardian.com/environment/climate-crisis/rss", "topic": "Climate"},
    {"name": "arXiv cs.AI", "url": "https://rss.arxiv.org/rss/cs.AI", "topic": "AI & Tech"},
]
PER_FEED_LIMIT = 20

# ---- Ranking ----
ARTICLE_MAX_AGE_HOURS = 72
MAX_PER_SOURCE = 3
INTEREST_THRESHOLD = 0.3      # weight above this counts as "a real interest"
EXPLORATION_SHARE = 0.15      # share of stories from outside the reader's bubble
STORIES_BY_MINUTES = {5: 8, 10: 14, 20: 24, 30: 32}
STYLE_COUNT_FACTOR = {"brief": 1.3, "balanced": 1.0, "in-depth": 0.7}
STYLE_SUMMARY_CHARS = {"brief": 150, "balanced": 260, "in-depth": 420}

# ---- Learning ----
SIGNAL_DELTAS = {"click": 0.08, "like": 0.12, "skip": -0.15, "less": -0.25}
NEW_TOPIC_START = 0.25
DAILY_DECAY = 0.98