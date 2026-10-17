"""
Onboarding: 4 short steps that build the reader's first interest profile.

  Step 1  Pick topics            (broad interests, fast)
  Step 2  Free text              (niche interests chips can't capture)
  Step 3  React to headlines     (reveals real taste)
  Step 4  Name + reading prefs   (then the user is saved)
"""
import streamlit as st

from core import config, ui
from core.db import create_user, init_db

init_db()
ui.inject_css()
st.markdown(
    """<div class="masthead"><h1>The Morning Paper</h1></div>
    <div class="dateline"><span>A paper of one</span><span>Two minutes</span>
    <span>Then, the news</span></div>""",
    unsafe_allow_html=True,
)

SAMPLE_HEADLINES = [
    ("New language model beats rivals on coding benchmarks", "AI & Tech"),
    ("Pakistan name squad for the home Test series", "Cricket"),
    ("Central bank holds interest rate steady", "Finance & Markets"),
    ("Floods raise fresh concerns over climate adaptation", "Climate"),
    ("Seed funding hits a record for local startups", "Startups"),
    ("Parliament debates the new budget proposals", "Pakistan Politics"),
    ("Researchers find a new link between sleep and memory", "Science"),
    ("Qualifying sets up a thrilling Grand Prix", "Formula 1"),
]

KEYWORDS = {
    "AI & Tech": ["ai", "tech", "software", "coding", "machine learning", "robot"],
    "Cricket": ["cricket", "psl", "test match", "babar"],
    "Football": ["football", "soccer", "premier league", "messi"],
    "Startups": ["startup", "funding", "venture", "founder"],
    "Pakistan Politics": ["politics", "parliament", "election", "government"],
    "Climate": ["climate", "environment", "weather", "green"],
    "Formula 1": ["formula 1", "f1", "grand prix"],
    "Finance & Markets": ["stock", "market", "crypto", "forex", "investing"],
    "Health": ["health", "fitness", "medicine", "nutrition"],
    "Science": ["science", "space", "physics", "research"],
    "Culture & Film": ["film", "movie", "cinema", "music", "festival"],
    "Education": ["school", "university", "exam", "students"],
    "World News": ["war", "un ", "geopolitics", "foreign policy"],
    "Business": ["business", "economy", "company", "inflation"],
}

st.subheader("Let's build your paper")

if "ob" not in st.session_state:
    st.session_state.ob = {"step": 1, "topics": [], "extra": [], "reactions": {}}
ob = st.session_state.ob

st.progress((ob["step"] - 1) / 4, text=f"Step {ob['step']} of 4")


def pick_topics():
    if hasattr(st, "pills"):
        return st.pills("Topics", config.TOPICS, selection_mode="multi",
                        default=ob["topics"], label_visibility="collapsed") or []
    return st.multiselect("Topics", config.TOPICS, default=ob["topics"],
                          label_visibility="collapsed")


if ob["step"] == 1:
    st.markdown("**What do you like reading about?**")
    st.caption("Pick at least three. These become the sections of your first edition.")
    chosen = pick_topics()
    if st.button("Next", type="primary", disabled=len(chosen) < 3):
        ob["topics"] = list(chosen)
        ob["step"] = 2
        st.rerun()

elif ob["step"] == 2:
    st.markdown("**Anything more specific?**")
    st.caption("Optional. Example: I follow Ferrari in Formula 1 and seed-stage climate startups.")
    text = st.text_area("Your interests", value=ob.get("text", ""),
                        label_visibility="collapsed")
    col1, col2 = st.columns(2)
    if col1.button("Back"):
        ob["step"] = 1
        st.rerun()
    if col2.button("Next", type="primary"):
        ob["text"] = text
        lowered = text.lower()
        ob["extra"] = [t for t, words in KEYWORDS.items()
                       if any(w in lowered for w in words) and t not in ob["topics"]]
        ob["step"] = 3
        st.rerun()

elif ob["step"] == 3:
    st.markdown("**Which of these would you actually read at breakfast?**")
    st.caption("A few honest reactions beat a long questionnaire.")
    liked_topics = set(ob["topics"]) | set(ob["extra"])
    ordered = sorted(SAMPLE_HEADLINES, key=lambda h: h[1] not in liked_topics)
    cards = ordered[:4] + ordered[-2:]
    answers = {}
    for i, (headline, topic) in enumerate(cards):
        st.markdown(f"**{headline}**")
        st.caption(topic)
        answers[(headline, topic)] = st.radio(
            headline, ["👍 Yes", "😐 Maybe", "👎 No"], index=1, horizontal=True,
            key=f"react_{i}", label_visibility="collapsed")
    col1, col2 = st.columns(2)
    if col1.button("Back"):
        ob["step"] = 2
        st.rerun()
    if col2.button("Next", type="primary"):
        ob["reactions"] = {topic: ans for (_, topic), ans in answers.items()}
        ob["step"] = 4
        st.rerun()

else:
    st.markdown("**Last step — how the paper should feel.**")
    name = st.text_input("What should we call you?")
    reading_time = st.select_slider("Time you have each morning (minutes)",
                                    options=[5, 10, 20, 30], value=10)
    style = st.radio("Reading style", ["Brief", "Balanced", "In-depth"],
                     index=1, horizontal=True)
    st.caption("Brief: more stories, shorter. In-depth: fewer stories, longer summaries.")

    col1, col2 = st.columns(2)
    if col1.button("Back"):
        ob["step"] = 3
        st.rerun()
    if col2.button("Create my paper", type="primary", disabled=not name.strip()):
        weights = {t: 0.7 for t in ob["topics"]}
        weights.update({t: 0.6 for t in ob["extra"]})
        for topic, ans in ob["reactions"].items():
            if "Yes" in ans:
                weights[topic] = min(1.0, weights.get(topic, 0.3) + 0.15)
            elif "No" in ans:
                weights[topic] = max(0.0, weights.get(topic, 0.3) - 0.2)
        weights = {t: round(w, 2) for t, w in weights.items() if w > 0}
        profile = {
            "weights": weights,
            "initial": dict(weights),
            "free_text": ob.get("text", ""),
        }
        user_id = create_user(name.strip(), reading_time, style.lower(), profile)
        st.session_state.user_id = user_id
        del st.session_state["ob"]
        st.switch_page("pages/2_Todays_Paper.py")
