"""Shared Streamlit pieces: newspaper CSS, masthead, story cards, full edition view."""
import html
import inspect

import streamlit as st

from core import db

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Source Serif 4', Georgia, serif; }
.masthead { text-align:center; border-top:4px double currentColor; border-bottom:4px double currentColor;
            padding:.3rem 0 .5rem; margin-bottom:.3rem; }
.masthead h1 { font-family:'Playfair Display', Georgia, serif; font-weight:900; font-size:3.4rem;
               margin:0; padding:0; letter-spacing:1px; }
.dateline { display:flex; justify-content:space-between; font-size:.8rem; text-transform:uppercase;
            letter-spacing:1px; border-bottom:1px solid currentColor; padding:.3rem 0; margin-bottom:1.2rem; }
.kicker { font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:#b3362d; margin-top:.4rem; }
.h-lead { font-family:'Playfair Display', Georgia, serif; font-weight:900; font-size:2.3rem; line-height:1.08; margin:.2rem 0 .3rem; }
.h-major { font-family:'Playfair Display', Georgia, serif; font-weight:700; font-size:1.3rem; line-height:1.15; margin:.1rem 0 .2rem; }
.h-std { font-family:'Playfair Display', Georgia, serif; font-weight:700; font-size:1.1rem; line-height:1.2; margin:.1rem 0 .2rem; }
.h-brief { font-weight:600; font-size:.98rem; line-height:1.25; }
.h-lead a, .h-major a, .h-std a, .h-brief a { color:inherit; text-decoration:none; }
.h-lead a:hover, .h-major a:hover, .h-std a:hover, .h-brief a:hover { text-decoration:underline; }
.byline { font-size:.78rem; opacity:.7; font-style:italic; margin-bottom:.35rem; }
.body { font-size:1rem; line-height:1.45; margin:.2rem 0 .4rem; }
.lead-img { width:100%; max-height:300px; object-fit:cover; margin:.3rem 0; }
.sec-title { text-transform:uppercase; letter-spacing:2px; font-weight:700; font-size:1rem;
             border-top:3px solid currentColor; border-bottom:1px solid currentColor; padding:.2rem 0; margin:1.6rem 0 .6rem; }
.sec-title small { text-transform:none; letter-spacing:0; font-weight:400; font-style:italic; opacity:.7; font-size:.8rem; }
.end-mark { text-align:center; letter-spacing:4px; opacity:.7; margin:2rem 0 .5rem; text-transform:uppercase; font-size:.85rem; }
</style>
"""

_LINK_BTN_HAS_CALLBACK = "on_click" in inspect.signature(st.link_button).parameters


DARK = """<style>
.stApp{background:#14161a;color:#ebe8e1}[data-testid=stSidebar]{background:#1b1e24}
[data-testid=stHeader]{background:transparent}.stApp [data-testid=stMarkdownContainer],.stApp label{color:#ebe8e1}
.kicker{color:#ff8a7a}.stApp [data-testid=stVerticalBlockBorderWrapper]{border-color:#3a3f48}
</style>"""
EXTRA = """<style>
.h-std,.h-major{transition:transform .15s}.h-std:hover,.h-major:hover{transform:translateX(3px)}
.stButton>button,.stLinkButton>a{border-radius:20px}
</style>"""


def _safe_url(u):
    return u if str(u).lower().startswith(("http://", "https://")) else "#"


def inject_css():
    dm = st.sidebar.toggle("🌙 Dark mode", value=st.session_state.get("dark_mode", False))
    st.session_state["dark_mode"] = dm
    st.markdown(CSS + EXTRA, unsafe_allow_html=True)
    if dm:
        st.markdown(DARK, unsafe_allow_html=True)


def require_user():
    """Return the signed-in reader, or stop the page with a friendly prompt."""
    db.init_db()
    uid = st.session_state.get("user_id")
    user = db.get_user(uid) if uid else None
    if not user:
        st.warning("Please choose a reader on the home page first.")
        if st.button("Go to the home page"):
            st.switch_page("app.py")
        st.stop()
    return user


def masthead(edition):
    st.markdown(
        f"""<div class="masthead"><h1>The Morning Paper</h1></div>
        <div class="dateline"><span>{html.escape(edition['date_long'])}</span>
        <span>Edition No. {edition['edition_no']}</span>
        <span>Prepared for {html.escape(edition['reader'])}</span></div>""",
        unsafe_allow_html=True)


def _read_button(story, user_id, key):
    aid = story["id"]
    log = lambda: db.log_event(user_id, aid, "click")
    if _LINK_BTN_HAS_CALLBACK:
        try:
            st.link_button("Read original ↗", _safe_url(story["url"]), on_click=log, key=f"{key}lb_{aid}")
            return
        except TypeError:
            pass
    opened = st.session_state.setdefault("opened", set())
    if aid in opened:  # two-step fallback for older Streamlit
        st.link_button("Open article ↗", _safe_url(story["url"]))
    elif st.button("Read original", key=f"{key}read_{aid}"):
        log()
        opened.add(aid)
        st.rerun()


def _story_card(story, user_id, size="standard", interactive=True, key=""):
    aid = story["id"]
    kicker = story["topic"] + (" · outside your usual topics" if story.get("explore") else "")
    cls = {"lead": "h-lead", "major": "h-major", "standard": "h-std", "brief": "h-brief"}[size]
    also = f" · also: {html.escape(', '.join(story['also']))}" if story.get("also") else ""
    parts = [f'<div class="kicker">{html.escape(kicker)}</div>',
             f'<div class="{cls}"><a href="{html.escape(_safe_url(story["url"]))}" target="_blank">'
             f'{html.escape(story["title"])}</a></div>',
             f'<div class="byline">{html.escape(story["source"] or "")} · {story["reading_min"]} min'
             f' · {story["published_label"]}{also}</div>']
    if size == "lead" and story.get("image"):
        parts.insert(2, f'<img class="lead-img" src="{html.escape(story["image"])}" alt="">')
    if size != "brief" and story.get("summary"):
        parts.append(f'<div class="body">{html.escape(story["summary"])}</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

    if not interactive or size == "brief":
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _read_button(story, user_id, key)
    with c2:
        liked = st.session_state.setdefault("liked", set())
        if aid in liked:
            st.button("Liked ✓", key=f"{key}liked_{aid}", disabled=True)
        elif st.button("👍 Like", key=f"{key}like_{aid}"):
            db.log_event(user_id, aid, "like")
            liked.add(aid)
            st.rerun(scope="fragment")
    with c3:
        if st.button("Skip", key=f"{key}skip_{aid}"):
            db.log_event(user_id, aid, "skip")
            st.rerun()
    with c4:
        if st.button("Less like this", key=f"{key}less_{aid}"):
            db.log_event(user_id, aid, "less")
            st.rerun()
    with st.expander("Why am I seeing this?"):
        st.write(story["why"])


def render_edition(edition, user_id, interactive=True, key=""):
    masthead(edition)
    hidden = db.user_action_ids(user_id, ["skip", "less"]) if interactive else set()
    visible = lambda stories: [s for s in stories if s["id"] not in hidden]

    front = visible([edition["lead"]] + edition["secondary"])
    if front:
        left, right = st.columns([2, 1])
        with left:
            story_card(front[0], user_id, "lead", interactive, key)
        with right:
            if edition["three_things"]:
                with st.container(border=True):
                    st.markdown("**Three things to know today**")
                    for i, t in enumerate(edition["three_things"], 1):
                        st.markdown(f"**{i}. {t['headline']}**  \n{t['takeaway']}")
            st.caption(f"{edition['stats']['stories']} stories · {edition['stats']['sources']} sources "
                       f"· about {edition['stats']['est_minutes']} min · {edition['style']} style")
        rest = front[1:]
        if rest:
            st.divider()
            for col, s in zip(st.columns(len(rest)), rest):
                with col:
                    story_card(s, user_id, "major", interactive, key)

    for sec in edition["sections"]:
        stories = visible(sec["stories"])
        if not stories:
            continue
        sub = " <small>something different, picked to widen your view</small>" if sec.get("explore") else ""
        st.markdown(f'<div class="sec-title">{html.escape(sec["name"])}{sub}</div>', unsafe_allow_html=True)
        n_cols = 1 if sec["size"] == "small" else 2
        for i in range(0, len(stories), n_cols):
            for col, s in zip(st.columns(n_cols), stories[i:i + n_cols]):
                with col:
                    story_card(s, user_id, "standard", interactive, key)

    briefs = visible(edition["briefs"])
    if briefs:
        st.markdown('<div class="sec-title">In brief</div>', unsafe_allow_html=True)
        for s in briefs:
            story_card(s, user_id, "brief", interactive, key)

    st.markdown('<div class="end-mark">✦ End of today\'s paper ✦</div>', unsafe_allow_html=True)
    st.caption("You're done. Nothing more to scroll. Headlines link to the original publishers.")
    if edition.get("editor_note"):
        st.markdown(f'*{edition["editor_note"]}*')
    if edition["learning_note"]:
        st.info("**How your paper is learning:** " + " ".join(edition["learning_note"]))

story_card = st.fragment(_story_card)  # clicks update one card, not the whole page
