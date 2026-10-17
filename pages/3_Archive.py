"""Past editions of this reader's paper — same JSON the PDF was typeset from."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Past papers", page_icon="📰", layout="wide")

from core import db, edition as ed, pdf, ui  # noqa: E402

user = ui.require_user()
uid = user["id"]
ui.inject_css()

st.markdown("### The bound volumes")
st.caption("Every morning's paper is kept. Open one, or take the PDF with you.")

rows = db.list_editions(uid)
if not rows:
    st.info("No editions yet. Read today's paper first — it will appear here afterwards.")
    st.stop()

labels = {f"No. {r['edition_no']}  ·  {r['date']}": r for r in rows}
choice = st.selectbox("Choose an edition", list(labels.keys()))
row = labels[choice]
json_path = Path(row["json_path"]) if row.get("json_path") else None
if not json_path or not json_path.exists():
    json_path, _ = ed.edition_paths(uid, row["date"])
if not json_path.exists():
    st.error("That edition file is missing from disk.")
    st.stop()

edition = ed.load_edition(json_path)

c1, c2, c3 = st.columns(3)
c1.metric("Stories", edition["stats"]["stories"])
c2.metric("Sources", edition["stats"]["sources"])
c3.metric("Est. minutes", edition["stats"]["est_minutes"])

pdf_file = pdf.pdf_path_for(edition)
if pdf_file.exists():
    st.download_button(
        "⬇ Download this edition as PDF",
        data=pdf_file.read_bytes(),
        file_name=f"morning-paper-{edition['date']}.pdf",
        mime="application/pdf",
    )
else:
    if st.button("Prepare PDF for this edition"):
        try:
            with st.spinner("Typesetting..."):
                pdf.render_pdf(edition)
            st.rerun()
        except RuntimeError as err:
            st.error(str(err))
            st.download_button(
                "Download printable HTML instead",
                data=pdf.render_html(edition),
                file_name=f"morning-paper-{edition['date']}.html",
                mime="text/html",
            )

st.divider()
ui.render_edition(edition, uid, interactive=False, key="arch_")
