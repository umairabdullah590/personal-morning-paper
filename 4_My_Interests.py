"""How the paper understands this reader — and a place to steer it by hand."""
import streamlit as st

st.set_page_config(page_title="My interests", page_icon="📰", layout="centered")

from core import config, db, edition as ed, learn, ui  # noqa: E402

user = ui.require_user()
uid = user["id"]
ui.inject_css()
profile = user["profile"]
weights = dict(profile.get("weights") or {})
initial = profile.get("initial") or dict(weights)
counts = db.event_counts(uid)

st.markdown("### How your paper is learning")
st.caption(
    "Likes, opens, skips and “less like this” nudge topic weights. "
    "Topics you never touch slowly fade. New topics appear when you engage with them."
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Opened", counts.get("click", 0))
c2.metric("Liked", counts.get("like", 0))
c3.metric("Skipped", counts.get("skip", 0))
c4.metric("Less like this", counts.get("less", 0))

if st.button("Apply feedback now", type="primary"):
    notes = learn.update_profile(uid)
    ed.build_edition(uid, rebuild=True)
    if notes:
        st.success("Updated:\n\n" + "\n".join(f"- {n}" for n in notes))
    else:
        st.info("Nothing new to learn yet. Read today's paper and react to a few stories.")

chart_rows = sorted(weights.items(), key=lambda kv: -kv[1])
if chart_rows:
    st.bar_chart(
        {
            "now": {t: w for t, w in chart_rows},
            "day one": {t: initial.get(t, 0) for t, _ in chart_rows},
        }
    )
else:
    st.info("No interest weights yet. Finish onboarding and rebuild today's paper.")

changes = profile.get("changes") or []
if changes:
    st.markdown("#### Recent shifts")
    for change in changes[:8]:
        st.write(f"- **{change.get('date', '')}** — {change.get('text', '')}")

st.divider()
st.markdown("#### Steer it yourself")
st.caption("Add a topic, remove one, or change how long you want to read.")

add = st.selectbox("Add a topic", [""] + [t for t in config.TOPICS if t not in weights])
if add and st.button("Follow this topic"):
    weights[add] = 0.65
    profile["weights"] = weights
    db.update_profile(uid, profile)
    st.rerun()

drop = st.multiselect("Topics to drop", list(weights.keys()))
if drop and st.button("Stop following selected"):
    for t in drop:
        weights.pop(t, None)
    profile["weights"] = weights
    db.update_profile(uid, profile)
    st.rerun()

name = st.text_input("Your name", value=user["name"])
reading_time = st.select_slider(
    "Morning minutes", options=[5, 10, 20, 30], value=user["reading_time"] or 10
)
styles = ["brief", "balanced", "in-depth"]
style = st.radio(
    "Reading style",
    styles,
    index=styles.index(user["style"]) if user["style"] in styles else 1,
    horizontal=True,
)
free_text = st.text_area(
    "Anything more specific (used to boost matching headlines)",
    value=profile.get("free_text", ""),
)
if st.button("Save preferences"):
    db.update_user(uid, name=name.strip() or user["name"],
                   reading_time=reading_time, style=style)
    profile["free_text"] = free_text
    db.update_profile(uid, profile)
    ed.build_edition(uid, rebuild=True)
    st.success("Saved. Today's paper will use the new preferences.")
