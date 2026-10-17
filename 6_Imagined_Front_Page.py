"""Imagined front page for any date - clearly fiction."""
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Imagined Front Page", page_icon="🔮", layout="centered")
from core import ui  # noqa: E402
from core.ai_news import generate_headlines_for, store_preview_for_user  # noqa: E402

user = ui.require_user()
ui.inject_css()
st.markdown("### 🔮 The Imagined Front Page")
st.warning("Everything here is invented by AI for fun. It is **not** real news.")
day = st.date_input("Pick any date", value=datetime.now().date())
if st.button("Imagine that morning", type="primary"):
    when = datetime.combine(day, datetime.min.time())
    with st.spinner("The newsroom is dreaming..."):
        heads = generate_headlines_for(when)
    store_preview_for_user(user["id"], when, heads)
    st.markdown(f'<div class="sec-title">{when:%A, %d %B %Y} · imagined</div>', unsafe_allow_html=True)
    for i, h in enumerate(heads, 1):
        st.markdown(f'<div class="h-major">{i}. {h}</div>', unsafe_allow_html=True)
