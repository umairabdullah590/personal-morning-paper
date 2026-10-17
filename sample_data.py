"""Offline demo articles so the whole product runs without internet.
These are PLACEHOLDERS (fake sources, example.com links), not real news."""
from datetime import timedelta

from core import db
from core.config import utcnow

SAMPLES = [
    # (title, source, snippet, hours_ago)
    ("Pakistan name squad for home Test series against England", "Sample Wire",
     "The selectors have named a 15-member squad for the opening Test, with two uncapped players included. The captain said the batting order is still open.", 3),
    ("Pakistan squad announced for England Test series", "Sample Times",
     "Pakistan have picked a 15-man group for the home Test series. Two newcomers are in the squad while a senior bowler misses out.", 5),
    ("Babar Azam returns to form with a century in domestic final", "Sample Daily",
     "The batter played a patient innings to lift his side to a comfortable win. Coaches said the knock should ease selection worries.", 8),
    ("PSL franchises debate new player draft rules", "Sample Wire",
     "Team owners met to discuss changes to the PSL player draft. A final decision is expected before the next season.", 20),
    ("New AI model beats rivals on coding benchmarks", "Sample Tech",
     "A new AI model has topped several public coding tests, according to its developers. Independent researchers say more testing is needed.", 2),
    ("Tech giants unveil new AI chatbot features for smartphones", "Sample Wire",
     "Several large firms announced chatbot tools built into their smartphone software. Analysts expect a fast rollout across new devices.", 4),
    ("Chip maker Nvidia shares climb as AI demand stays strong", "Sample Times",
     "Shares rose after the company said demand for AI chips remains high. Investors are watching supply limits closely.", 6),
    ("Researchers warn of rising cyber attacks on hospital networks", "Sample Daily",
     "A new report says hospital networks are facing more frequent cyber attacks. Experts urge basic fixes such as software updates and backups.", 12),
    ("Open-source software project doubles contributors in a year", "Sample Tech",
     "The community project says it has doubled its number of contributors. Maintainers credit better onboarding guides.", 26),
    ("Pakistani startup raises seed funding for farm logistics", "Sample Tech",
     "A young company building cold-chain logistics for farmers has closed a seed funding round. It plans to expand to three new regions.", 5),
    ("Venture funding for climate startups hits a record", "Sample Wire",
     "Investors put more money into climate startups this year than ever before. Battery and grid projects drew the biggest cheques.", 9),
    ("Founder of delivery startup steps down after funding round", "Sample Daily",
     "The founder will move to an advisory role as the company grows. A new chief executive starts next month.", 22),
    ("State Bank holds interest rate steady as inflation eases", "Sample Times",
     "The central bank kept its policy interest rate unchanged. Officials said inflation is cooling but risks remain.", 4),
    ("Rupee gains against the dollar in interbank trading", "Sample Wire",
     "The rupee edged higher against the dollar in early trading. Dealers pointed to steady inflows and lower import demand.", 6),
    ("Stocks close higher as KSE-100 extends rally", "Sample Daily",
     "The benchmark index rose for a third straight session. Banks and energy firms led the gains.", 3),
    ("Bitcoin slips as investors await central bank signals", "Sample Tech",
     "The crypto market cooled as traders waited for policy clues. Trading volumes were lower than last week.", 10),
    ("National Assembly debates new budget proposals", "Sample Times",
     "Lawmakers began debating the proposed budget, with the opposition raising concerns about taxes. A vote is expected later this week.", 5),
    ("Senate committee reviews election reform bill", "Sample Daily",
     "A Senate committee started a clause-by-clause review of the election reform bill. Members asked for more time to study the changes.", 11),
    ("Supreme Court hears petition on local government powers", "Sample Wire",
     "A bench heard arguments on how much power local governments should hold. The hearing was adjourned until next week.", 15),
    ("Ceasefire talks resume as United Nations urges aid access", "Sample Wire",
     "Negotiators returned to the table as the United Nations pressed for safe aid routes. Officials described the talks as difficult.", 2),
    ("Ceasefire talks continue with United Nations mediators", "Sample Times",
     "Mediators from the United Nations are helping both sides draft terms. Aid agencies say needs are growing quickly.", 3),
    ("Leaders gather for summit on sanctions and trade", "Sample Daily",
     "Heads of government met to discuss sanctions policy and trade rules. A joint statement is expected on the final day.", 7),
    ("Floods displace thousands as monsoon rains intensify", "Sample Times",
     "Heavy monsoon rain has pushed rivers over their banks, forcing thousands to leave their homes. Relief camps have been set up in several districts.", 4),
    ("Heatwave drives record demand for solar power", "Sample Daily",
     "A prolonged heatwave pushed electricity demand to a new high. Solar output covered a larger share than in previous summers.", 13),
    ("Emissions fall in major economies, new report finds", "Sample Wire",
     "A new report says emissions dropped in several large economies. The authors say the pace is still too slow for climate targets.", 18),
    ("Dengue cases rise as hospitals prepare for peak season", "Sample Daily",
     "Health officials reported a steady rise in dengue cases. Hospitals are adding beds and urging people to remove standing water.", 6),
    ("Researchers link regular sleep to better memory in adults", "Sample Tech",
     "A study of several thousand adults found that steady sleep patterns were tied to better recall. The authors say more work is needed to show cause.", 9),
    ("Telescope captures new images of distant galaxy cluster", "Sample Wire",
     "Astronomers released new images of a galaxy cluster billions of light years away. The pictures help map how matter is spread across space.", 7),
    ("Scientists discover new species in deep-sea expedition", "Sample Times",
     "A research team described several previously unknown species found on a deep-sea survey. Samples are being studied in labs.", 21),
    ("University entrance exams to be held online, officials say", "Sample Daily",
     "Officials said university entrance exams will move online from next year. Students will get practice tests beforehand.", 10),
    ("HEC announces new scholarship scheme for students", "Sample Times",
     "The commission announced a scholarship scheme aimed at students from rural areas. Applications open next month.", 25),
    ("Festival opens with a new Pakistani drama film", "Sample Wire",
     "The festival opened with a drama film from a first-time director. Critics praised its performances and cinematography.", 8),
    ("Album release breaks streaming records for the year", "Sample Daily",
     "A new album set a record for first-day streams this year. Its lead single has already topped several charts.", 16),
    ("Premier League title race tightens after a late winner", "Sample Times",
     "A stoppage-time goal cut the gap at the top of the Premier League table. The leaders face a tough away trip next.", 5),
    ("Striker signs new contract with Champions League side", "Sample Wire",
     "The club announced a new long-term deal for its leading striker. The player said he wants to win more trophies.", 14),
    ("Verstappen takes pole as qualifying sets up Grand Prix", "Sample Daily",
     "Verstappen set the fastest lap in qualifying to start from pole. Rivals said tyre wear could shake up the race.", 6),
    ("Ferrari bring major upgrade package to the Grand Prix", "Sample Times",
     "Ferrari introduced a large aerodynamic upgrade for this weekend. The team hopes it closes the gap to the front.", 18),
]


def load():
    """Insert the sample articles (safe to run more than once). Returns count of new ones."""
    now = utcnow()
    new = 0
    for i, (title, source, snippet, hours) in enumerate(SAMPLES, start=1):
        published = (now - timedelta(hours=hours)).isoformat(timespec="seconds")
        new += db.upsert_article({
            "url": f"https://example.com/sample/{i}", "title": title, "source": source,
            "published": published, "snippet": snippet, "image": None, "hint_topic": None,
        })
    return new