"""Imagined front pages: Claude if a key is set, otherwise an offline generator.
Always labelled as fiction - these are NOT real news."""
import json
import random
import re
from datetime import datetime

from core import config
from core.db import get_user, update_profile

_BEATS = {
    "Politics": ["Parliament delays vote on {x}", "Coalition talks stall over {x}"],
    "Technology": ["Startup unveils {x} assistant for classrooms", "Engineers demo {x} on a budget phone"],
    "Culture": ["Festival opens with a film about {x}", "Debut novel on {x} tops the charts"],
    "Science": ["Researchers report surprising link between {x} and sleep", "Telescope team studies {x}"],
    "Sports": ["Underdogs stun favourites in {x} final", "Veteran captain eyes {x} record"],
}
_X = ["clean water", "river tides", "open data", "night markets", "solar roofs", "deep-sea maps"]


def generate_headlines_for(date: datetime) -> list[str]:
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            msg = client.messages.create(
                model=config.LLM_MODEL, max_tokens=300,
                messages=[{"role": "user", "content":
                           f"Invent five fictional newspaper headlines for {date:%A, %d %B %Y} "
                           "(politics, tech, culture, science, sport). Plainly fictional, no real people. "
                           'Reply ONLY with a JSON list of 5 strings.'}])
            data = json.loads(re.search(r"\[.*\]", msg.content[0].text, re.S).group(0))
            if data:
                return [str(h) for h in data][:5]
        except Exception:
            pass
    rng = random.Random(date.toordinal())
    return [rng.choice(v).format(x=rng.choice(_X)) for v in _BEATS.values()]


def store_preview_for_user(user_id, date, headlines):
    profile = (get_user(user_id) or {}).get("profile", {})
    profile["preview"] = {"date": date.isoformat(), "headlines": headlines}
    update_profile(user_id, profile)
