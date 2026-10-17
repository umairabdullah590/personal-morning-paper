# 📰 The Morning Paper

**One finite, personal newspaper, made for you every morning.**

Most news apps are endless feeds. The Morning Paper builds a single edition sized to the time you have (5 to 30 minutes), learns from how you read, and ends with *"You're done."*

## ✨ Features

- **Personalised front page**: your interests decide the lead story, section order, section size and summary length.
- **Learns from you**: likes, opens, skips and "less like this" nudge your topic weights. Unread topics fade over time.
- **Explainable**: every story has a "Why am I seeing this?" panel, and *My Interests* shows how your profile shifted.
- **Beyond Your Bubble**: about 15% of stories come from outside your topics, to avoid an echo chamber.
- **Ask the Paper** 💬: chat with today's edition. Answers come only from the printed stories and cite them.
- **Imagined Front Page** 🔮: AI-invented headlines for any date, clearly labelled as fiction.
- **Newspaper-style PDF** of every edition, plus an archive of past papers.
- **Dark mode**, and a snappy UI where clicking Like updates one card, not the whole page.
- **Works offline**: sample data and keyword fallbacks mean no API key is required.

## 🧠 How it works

```
RSS feeds → fetch → enrich → rank → edition (JSON) → web page + PDF
                                  ↑                        │
                                  └──── learn ◄── likes / skips / clicks
```

| Step | File | What it does |
|------|------|--------------|
| Fetch | `core/fetch.py` | Pulls ~18 RSS feeds in parallel (Dawn, BBC, Al Jazeera, The Verge, and more). |
| Enrich | `core/enrich.py` | Tags topics, writes a short summary, estimates reading time, scores importance by how many outlets cover a story. Uses Claude if a key is set, otherwise keyword rules. |
| Rank | `core/rank.py` | Scores articles per reader (interest, importance, freshness, free-text match), merges duplicate stories and caps any one source. |
| Edition | `core/edition.py` | Builds one JSON edition that both the web page and PDF render from. |
| Learn | `core/learn.py` | Click +0.08, like +0.12, skip −0.15, less −0.25, with a 0.98 daily decay. |
| PDF | `core/pdf.py` | Typesets the edition with WeasyPrint. |

## 🚀 Quick start

```bash
git clone https://github.com/<your-username>/personal-morning-paper.git
cd personal-morning-paper
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Optional: enable Claude features.

```bash
cp .env.example .env            # then paste your key after ANTHROPIC_API_KEY=
```

Load demo data (works offline) and launch:

```bash
python rundaily.py --sample --no-pdf
streamlit run app.py
```

For live news instead, run `python rundaily.py`, or click **Fetch latest news** in the app.

### PDF note (Windows)
WeasyPrint needs the GTK runtime on Windows. If it isn't installed, the app offers a printable HTML download instead.

### Daily schedule
Run `python rundaily.py` from cron or Task Scheduler (for example at 05:00) so your paper is ready each morning.

## 🗂 Project structure

```
app.py                  Home page and reader selection
pages/
  1_Onboarding.py       4-step interest setup
  2_Todays_Paper.py     Today's edition, feedback, PDF download
  3_Archive.py          Past editions
  4_My_Interests.py     How the paper is learning, manual steering
  5_Ask_the_Paper.py    Chat with today's edition
  6_Imagined_Front_Page.py  Fictional headlines for any date
core/                   Pipeline and shared UI
templates/              PDF layout (paper.html, paper.css)
data/                   SQLite database and saved editions (git-ignored)
rundaily.py             Full pipeline, for scheduling
```

## ⚙️ Configuration

| Setting | Where | Default |
|---------|-------|---------|
| `ANTHROPIC_API_KEY` | `.env` or environment | empty (offline mode) |
| `PAPER_LLM_MODEL` | environment | `claude-haiku-5-5` |
| Topics, feeds, ranking and learning constants | `core/config.py` | see file |

## 🔒 Security

Never commit API keys. `.env` and the database are in `.gitignore`. If a key has ever been pushed, revoke it.

## 📜 Notes

Headlines and short summaries link to the original publishers. *Imagined Front Page* content is fictional and not real news.

## 🛣 Ideas for next steps

- Smarter topic tagging (for example, separating cricket from politics)
- Decay only topics you stop reading
- Audio briefing of the three key stories
- Email or WhatsApp delivery of the PDF

