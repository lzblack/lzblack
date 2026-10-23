"""Put today's connections puzzles (English and Chinese) into README.md.

Run by .github/workflows/connections.yml. Standard library only. The README is
rewritten only between the connections markers, and only when both puzzles
fetch and validate; on any failure it exits non-zero and leaves the file alone.
"""
from __future__ import annotations

import html
import json
import random
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

API = "https://connections.zhili.dev/api/puzzles/{lang}/{date}"
PLAY = "https://connections.zhili.dev/"
# Same zones as connections-game's src/lib/daily.ts: each language's puzzle
# changes at local midnight.
TIMEZONE = {"en": "America/New_York", "zh": "Asia/Shanghai"}
START, END = "<!-- connections:start -->", "<!-- connections:end -->"
MAX_WORD = 40


def daily_date(lang: str, now: datetime) -> str:
    return now.astimezone(ZoneInfo(TIMEZONE[lang])).date().isoformat()


def fetch(lang: str, date: str) -> object:
    req = urllib.request.Request(API.format(lang=lang, date=date), headers={"User-Agent": "lzblack-profile-readme"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def words(p: object, lang: str, date: str) -> list[str]:
    """The sixteen words of a puzzle, after checking it is the one asked for."""
    if not isinstance(p, dict):
        raise ValueError("puzzle is not an object")
    if p.get("language") != lang or p.get("date") != date:
        raise ValueError(f"expected {lang} {date}, got {p.get('language')} {p.get('date')}")
    groups = p.get("groups")
    if not isinstance(groups, list) or len(groups) != 4:
        raise ValueError("expected four groups")
    out: list[str] = []
    for g in groups:
        ws = g.get("words") if isinstance(g, dict) else None
        if not isinstance(ws, list) or len(ws) != 4:
            raise ValueError("expected four words per group")
        for w in ws:
            if not isinstance(w, str) or not w.strip() or len(w) > MAX_WORD:
                raise ValueError(f"bad word: {w!r}")
            out.append(w.strip())
    if len(set(out)) != 16:
        raise ValueError("words are not all different")
    return out


def shuffle(ws: list[str], seed: str) -> list[str]:
    # A string seed gives the same order on every run and Python version 3.x,
    # so a re-run on the same day leaves the README unchanged.
    out = list(ws)
    random.Random(seed).shuffle(out)
    return out


def grid(ws: list[str]) -> str:
    rows = ("<tr>" + "".join(f"<td>{html.escape(w)}</td>" for w in ws[i:i + 4]) + "</tr>" for i in range(0, 16, 4))
    return "<table>" + "".join(rows) + "</table>"


def section(en: list[str], zh: list[str]) -> str:
    return (
        "<details>\n<summary><b>Today's connections</b></summary>\n\n"
        '<table><tr><td valign="top">\n\n'
        f"[**English**]({PLAY})\n\n{grid(en)}\n\n"
        '</td><td valign="top">\n\n'
        f"[**中文**]({PLAY})\n\n{grid(zh)}\n\n"
        "</td></tr></table>\n\n</details>"
    )


def replace_section(text: str, block: str) -> str:
    if text.count(START) != 1 or text.count(END) != 1 or text.index(START) > text.index(END):
        raise ValueError("README needs exactly one connections:start / connections:end pair, in that order")
    head, rest = text.split(START)
    _, tail = rest.split(END)
    return f"{head}{START}\n{block}\n{END}{tail}"


def main(readme: Path) -> int:
    now = datetime.now(timezone.utc)
    picked = {}
    for lang in ("en", "zh"):
        date = daily_date(lang, now)
        try:
            picked[lang] = shuffle(words(fetch(lang, date), lang, date), f"{lang} {date}")
        except Exception as e:  # network, JSON or shape: report and leave the README as it is
            print(f"connections {lang} {date}: {e}", file=sys.stderr)
            return 1
    old = readme.read_text(encoding="utf-8")
    new = replace_section(old, section(picked["en"], picked["zh"]))
    if new != old:
        readme.write_text(new, encoding="utf-8")
        print("README updated")
    else:
        print("README unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "README.md")))
