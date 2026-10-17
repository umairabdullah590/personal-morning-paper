"""Today's edition: read it, give feedback, download the PDF."""
import streamlit as st

st.set_page_config(page_title="Today's Paper", page_icon="📰", layout="wide")

from core import db, edition as ed, enrich, fetch, learn, pdf, sample_data, ui  # noqa: E402

user = ui.require_user()
uid = user["id"]
ui.inject_css()

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown(f"**Reader:** {user['name']}")
    if st.button("Fetch latest news", use_container_width=True):
        with st.spinner("Collecting stories from your sources..."):
            new, ok, failed = fetch.fetch_all()
            enrich.run()
        st.success(f"{new} new articles ({ok} feeds ok, {failed} failed).")
    if st.button("Apply my feedback & rebuild", use_container_width=True,
                 help="Learns from your likes, skips and clicks, then rebuilds today's paper."):
        st.session_state["learn_notes"] = learn.update_profile(uid)
        ed.build_edition(uid, rebuild=True)
        st.rerun()

# ---------------- need articles first ----------------
if db.count_articles() == 0:
    st.info("There are no articles yet. Fetch live news, or load the offline sample articles for a demo.")
    c1, c2 = st.columns(2)
    if c1.button("Fetch live news", type="primary"):
        with st.spinner("Fetching..."):
            fetch.fetch_all()
            enrich.run()
        st.rerun()
    if c2.button("Load sample articles"):
        sample_data.load()
        enrich.run()
        st.rerun()
    st.stop()

edition = ed.build_edition(uid)
if edition is None:
    st.warning("No fresh, unread articles match yet. Try 'Fetch latest news' in the sidebar.")
    st.stop()

notes = st.session_state.pop("learn_notes", None)
if notes is not None:
    if notes:
        st.success("Your paper learned from your activity:\n\n" + "\n".join(f"- {n}" for n in notes))
    else:
        st.info("No new signals yet. Like, skip or open a few stories, then rebuild.")

# ---------------- PDF ----------------
with st.sidebar:
    st.divider()
    pdf_file = pdf.pdf_path_for(edition)
    if pdf_file.exists():
        st.download_button("⬇ Download PDF edition", data=pdf_file.read_bytes(),
                           file_name=f"morning-paper-{edition['date']}.pdf", mime="application/pdf",
                           use_container_width=True,
                           on_click=lambda: db.log_event(uid, None, "download"))
    elif st.button("Prepare PDF edition", use_container_width=True):
        try:
            with st.spinner("Typesetting your paper..."):
                pdf.render_pdf(edition)
            st.rerun()
        except RuntimeError as err:
            st.error(str(err))
            st.download_button("Download printable HTML instead", data=pdf.render_html(edition),
                               file_name=f"morning-paper-{edition['date']}.html", mime="text/html")

ui.render_edition(edition, uid, interactive=True, key="today_")