"""Step 5: render an edition (JSON dict) as a newspaper-style PDF with WeasyPrint."""
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core import db
from core.config import TEMPLATES_DIR
from core.edition import edition_paths

_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)),
                   autoescape=select_autoescape(["html"]))


def render_html(edition):
    return _env.get_template("paper.html").render(e=edition)


def pdf_path_for(edition):
    return edition_paths(edition["user_id"], edition["date"])[1]


def render_pdf(edition):
    """Write the PDF and return its path. Raises RuntimeError if WeasyPrint is not usable."""
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as err:
        raise RuntimeError(
            "WeasyPrint is not available. Install it with `pip install weasyprint` "
            "(on Windows it also needs the GTK runtime). Details: " + str(err))
    path = pdf_path_for(edition)
    HTML(string=render_html(edition), base_url=str(TEMPLATES_DIR)).write_pdf(str(path))
    db.set_pdf_path(edition["user_id"], edition["date"], path)
    return path


def ensure_pdf(edition):
    path = pdf_path_for(edition)
    return path if path.exists() else render_pdf(edition)