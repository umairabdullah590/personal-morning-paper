"""The Morning Paper - entry point.  Run with:  streamlit run app.py"""
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="The Morning Paper", page_icon="📰", layout="centered")
from core import ui  # noqa: E402
from core.db import event_counts, count_editions, get_user, init_db, list_users, set_user_pref  # noqa: E402

init_db()
ui.inject_css()
st.session_state.setdefault("user_id", None)
users = list_users()
today = datetime.now().strftime("%A, %d %B %Y")
current = get_user(st.session_state.user_id) if st.session_state.user_id else None


def masthead(sub):
    st.markdown(f'<div class="masthead"><h1>The Morning Paper</h1></div>'
                f'<div class="dateline"><span>{today}</span><span>{sub}</span></div>', unsafe_allow_html=True)


def tagline(t):
    st.markdown(f'<div class="h-major" style="text-align:center;font-style:italic">{t}</div>', unsafe_allow_html=True)


if not users:
    masthead("Welcome")
    tagline("One finite paper, made for you, every morning.")
    st.write("Tell us what you care about in under two minutes and we'll gather the stories that matter.")
    if st.button("Create my paper", type="primary", use_container_width=True):
        st.switch_page("pages/1_Onboarding.py")
elif current is None:
    masthead("Welcome back")
    tagline("Who is reading today?")
    names = {u["name"]: u["id"] for u in users}
    choice = st.selectbox("Choose your name", list(names))
    c1, c2 = st.columns(2)
    if c1.button("Open my paper", type="primary", use_container_width=True):
        st.session_state.user_id = names[choice]
        st.session_state["dark_mode"] = bool(get_user(names[choice]).get("dark_mode"))
        st.rerun()
    if c2.button("I'm new here", use_container_width=True):
        st.switch_page("pages/1_Onboarding.py")
else:
    set_user_pref(current["id"], bool(st.session_state.get("dark_mode")))
    masthead(f"Edition for {current['name']}")
    tagline(f"Good morning, {current['name']}.")
    n = event_counts(current["id"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Editions read", count_editions(current["id"]))
    m2.metric("Stories liked", n.get("like", 0))
    m3.metric("Stories opened", n.get("click", 0))
    pages = [("📰 Today's paper", "pages/2_Todays_Paper.py"), ("💬 Ask the Paper", "pages/5_Ask_the_Paper.py"),
             ("🧠 My interests", "pages/4_My_Interests.py"), ("🗄 Past papers", "pages/3_Archive.py"),
             ("🔮 Imagined front page", "pages/6_Imagined_Front_Page.py")]
    for (label, target), col in zip(pages, st.columns(len(pages)) if False else [None] * len(pages)):
        pass
    for i in range(0, len(pages), 2):
        for col, (label, target) in zip(st.columns(2), pages[i:i + 2]):
            if col.button(label, use_container_width=True, type="primary" if i == 0 and label.startswith("📰") else "secondary"):
                st.switch_page(target)
    st.divider()
    if st.button("Switch reader"):
        st.session_state.user_id = None
        st.rerun()
