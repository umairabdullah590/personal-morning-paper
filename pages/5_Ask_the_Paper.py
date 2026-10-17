"""Chat with today's edition. Claude answers from the printed stories only;
without an API key it falls back to keyword search over the same stories."""
import streamlit as st

st.set_page_config(page_title="Ask the Paper", page_icon="💬", layout="centered")
from core import config, edition as ed, enrich, ui  # noqa: E402

user = ui.require_user()
ui.inject_css()
st.markdown("### 💬 Ask the Paper")
e = ed.build_edition(user["id"])
if e is None:
    st.info("No edition yet. Open today's paper first.")
    st.stop()

stories = [e["lead"]] + e["secondary"] + [s for sec in e["sections"] for s in sec["stories"]] + e["briefs"]
stories = [s for s in stories if s.get("summary") and s["summary"] != "…"]


def answer(q):
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            ctx = "\n".join(f"[{i}] {s['title']} ({s['source']}): {s['summary']}" for i, s in enumerate(stories, 1))
            m = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY).messages.create(
                model=config.LLM_MODEL, max_tokens=500,
                system="You are the editor of this reader's personal paper. Answer ONLY from the stories "
                       "below, cite them like [2], and say so if they don't cover the question. Be concise.\n\n" + ctx,
                messages=[{"role": "user", "content": q}])
            return m.content[0].text
        except Exception:
            pass
    qt = enrich.tokens(q)
    top = sorted(stories, key=lambda s: -enrich.jaccard(qt, enrich.tokens(s["title"] + " " + s["summary"])))[:3]
    return "Closest stories in today's paper (add an ANTHROPIC_API_KEY for real answers):\n\n" + "\n\n".join(
        f"**{s['title']}** ({s['source']})  \n{s['summary']}" for s in top)


st.caption("Answers come only from the stories in today's edition.")
chat = st.session_state.setdefault("chat", [])
for role, text in chat:
    st.chat_message(role).write(text)
c1, c2, c3 = st.columns(3)
quick = None
if c1.button("Summarise in 3 lines"):
    quick = "Summarise today's paper in three lines."
if c2.button("What matters most?"):
    quick = "Which story matters most to me and why?"
if c3.button("Explain it simply"):
    quick = "Explain the lead story as if I'm new to the topic."
q = quick or st.chat_input("Ask about today's stories...")
if q:
    chat.append(("user", q))
    chat.append(("assistant", answer(q)))
    st.rerun()
