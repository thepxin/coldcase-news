"""Hard, non-AI checks run on every article before it can be published.

An article is rejected (not fixed) if ANY of these fail:
  1. Links: every link points to one of the approved sources it was written from. No other links.
  2. Numbers: every figure (counts, money, percentages) appears in at least one source.
  3. Dates and years: every date and year matches one in a source, or a source's publication date.
  4. CVE IDs: every CVE ID appears in a source.
  5. No conclusions: no lesson, opinion or prediction phrasing.
These rules are deliberately strict: when in doubt, the article is not published.
"""
import re

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}
MONTHS.update({m[:3]: i for m, i in list(MONTHS.items())})
MONTHS["sept"] = 9
WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
                "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100, "dozen": 12}
MULT = {"thousand": 1e3, "k": 1e3, "million": 1e6, "m": 1e6, "mn": 1e6, "billion": 1e9, "bn": 1e9, "b": 1e9, "trillion": 1e12, "tn": 1e12}
OPINION = re.compile(
    r"\b(lessons?|takeaways?|we believe|in our view|we think|should consider|it is likely|will likely|probably|"
    r"it remains to be seen|this shows that|this highlights|highlights the|underscores|serves as a reminder|wake-up call|"
    r"needless to say|clearly demonstrates|proves that)\b", re.I)

MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
BARE_URL = re.compile(r"https?://[^\s)\]>\"']+")
CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
ISO_DATE = re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
MONTH_NAMES = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
MDY = re.compile(MONTH_NAMES + r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+((?:19|20)\d{2}))?\b", re.I)
DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + MONTH_NAMES + r"\.?,?(?:\s+((?:19|20)\d{2}))?\b", re.I)
YEAR = re.compile(r"(?<![\d\-/.])((?:19|20)\d{2})(?![\d\-/])")
NUMBER = re.compile(
    r"(?<![\w.\-/])([$€£₹])?\s?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s?(%|percent\b|per cent\b|"
    r"thousand\b|million\b|billion\b|trillion\b|mn\b|bn\b|tn\b|[kKmMbB]\b)?", re.I)
WORD_NUMBER = re.compile(r"\b(" + "|".join(WORD_NUMBERS) + r")\b(?:\s+(thousand|million|billion|trillion))?", re.I)


def _norm_url(u):
    return u.strip().rstrip("/.,;:").lower()


def _strip_for_numbers(text):
    t = MD_LINK.sub("]()", text)
    t = BARE_URL.sub(" ", t)
    t = CVE.sub(" ", t)
    t = ISO_DATE.sub(" ", t)
    t = MDY.sub(" ", t)
    t = DMY.sub(" ", t)
    t = YEAR.sub(" ", t)
    t = re.sub(r"\b\d{1,2}:\d{2}\b", " ", t)  # clock times
    t = re.sub(r"(?m)^\s*\d+\.\s", " ", t)  # numbered list markers
    return t


def _values(text, include_words=False):
    vals = set()
    for cur, num, unit in NUMBER.findall(text):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        u = (unit or "").lower().strip()
        if u in ("%", "percent", "per cent"):
            vals.add(("pct", round(v, 4)))
            continue
        v = v * MULT.get(u, 1)
        vals.add(("num", round(v, 4)))
    if include_words:
        for w, unit in WORD_NUMBER.findall(text):
            v = WORD_NUMBERS[w.lower()] * MULT.get((unit or "").lower(), 1)
            vals.add(("num", round(v, 4)))
    return vals


def _dates(text):
    full, partial, years = set(), set(), set()
    for m in ISO_DATE.finditer(text):
        y, mo, d = map(int, m.group(0).split("-"))
        full.add((y, mo, d))
    for mname, d, y in MDY.findall(text):
        mo, d = MONTHS[mname.lower()[:3]], int(d)
        if 1 <= d <= 31:
            (full.add((int(y), mo, d)) if y else partial.add((mo, d)))
    for d, mname, y in DMY.findall(text):
        mo, d = MONTHS[mname.lower()[:3]], int(d)
        if 1 <= d <= 31:
            (full.add((int(y), mo, d)) if y else partial.add((mo, d)))
    years.update(int(y) for y in YEAR.findall(text))
    return full, partial, years


def check_article(article_texts, sources):
    """article_texts: list of strings (headline, then, now, body...). Returns a list of problems (empty = pass)."""
    problems = []
    text = "\n".join(article_texts)
    src_text = "\n".join((s.get("title") or "") + "\n" + (s.get("excerpt") or "") for s in sources)
    src_urls = {_norm_url(s["url"]) for s in sources}

    # 1. links
    for u in set(MD_LINK.findall(text)) | set(BARE_URL.findall(MD_LINK.sub("]()", text))):
        if u.startswith("/go/") or "coldcasetech.com/go/" in u:
            problems.append(f"affiliate link inside the reporting: {u}")
        elif _norm_url(u) not in src_urls:
            problems.append(f"link not among the approved sources: {u}")

    # 2. CVE IDs
    src_cves = {c.upper() for c in CVE.findall(src_text)}
    for c in {c.upper() for c in CVE.findall(text)} - src_cves:
        problems.append(f"CVE ID not in any source: {c}")

    # 3. dates and years
    s_full, s_partial, s_years = _dates(src_text)
    for s in sources:
        m = ISO_DATE.search(s.get("date") or "")
        if m:
            y, mo, d = map(int, m.group(0).split("-"))
            s_full.add((y, mo, d))
            s_years.add(y)
    s_years |= {y for y, _, _ in s_full}
    a_full, a_partial, a_years = _dates(MD_LINK.sub("]()", text))
    for (y, mo, d) in a_full:
        if (y, mo, d) not in s_full and not ((mo, d) in s_partial and y in s_years):
            problems.append(f"date not found in sources: {y:04d}-{mo:02d}-{d:02d}")
    for (mo, d) in a_partial:
        if (mo, d) not in s_partial and not any((m2, d2) == (mo, d) for _, m2, d2 in s_full):
            problems.append(f"date not found in sources: month {mo}, day {d}")
    stripped_years_text = ISO_DATE.sub(" ", MDY.sub(" ", DMY.sub(" ", MD_LINK.sub("]()", text))))
    for y in {int(y) for y in YEAR.findall(stripped_years_text)}:
        if y not in s_years:
            problems.append(f"year not found in sources: {y}")

    # 4. numbers
    src_vals = _values(_strip_for_numbers(src_text), include_words=True)
    for kind, v in sorted(_values(_strip_for_numbers(text))):
        if (kind, v) not in src_vals:
            shown = f"{v:g}%" if kind == "pct" else (f"{v:,.0f}" if v == int(v) else f"{v:,}")
            problems.append(f"figure not found in any source: {shown}")

    # 5. conclusions / opinion
    for m in sorted({m.group(0).lower() for m in OPINION.finditer(MD_LINK.sub("]()", text))}):
        problems.append(f"conclusion or opinion wording: '{m}'")
    return problems
