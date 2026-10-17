"""Run the whole pipeline: fetch -> enrich -> learn -> build editions -> PDFs.

    python run_daily.py              # live feeds
    python run_daily.py --sample     # offline demo articles
    python run_daily.py --no-pdf     # skip PDF rendering

Schedule it (cron / Task Scheduler) for early morning, e.g. 05:00.
"""
import argparse

from core import db, edition, enrich, fetch, learn, pdf, sample_data


def main(sample=False, make_pdf=True):
    db.init_db()
    if sample:
        print(f"Loaded {sample_data.load()} sample articles")
    else:
        new, ok, failed = fetch.fetch_all()
        print(f"Fetched {new} new articles ({ok} feeds ok, {failed} failed)")
    print(f"Enriched {enrich.run()} articles")

    for user in db.list_users():
        notes = learn.update_profile(user["id"])
        ed = edition.build_edition(user["id"], rebuild=True)
        if ed is None:
            print(f"- {user['name']}: no articles available")
            continue
        line = f"- {user['name']}: edition No. {ed['edition_no']}, {ed['stats']['stories']} stories"
        if make_pdf:
            try:
                line += f", PDF {pdf.render_pdf(ed).name}"
            except RuntimeError as err:
                line += f", PDF skipped ({err})"
        print(line)
        for n in notes:
            print(f"    learned: {n}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    p.add_argument("--no-pdf", action="store_true")
    a = p.parse_args()
    main(sample=a.sample, make_pdf=not a.no_pdf)