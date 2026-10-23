from datetime import datetime, timezone

import pytest

from scripts import connections as c

GROUPS = [
    {"words": ["MIRROR", "GLASS", "WINDOW", "LENS"]},
    {"words": ["PILLOW", "BLANKET", "SHEET", "QUILT"]},
    {"words": ["GLOVE", "SCARF", "BOOT", "JACKET"]},
    {"words": ["BRICK", "TILE", "BEAM", "PLANK"]},
]


def puzzle(**over):
    p = {"language": "en", "date": "2026-10-23", "groups": GROUPS}
    p.update(over)
    return p


# daily_date: each language rolls over at midnight in its own time zone,
# matching connections-game's src/lib/daily.ts.

def test_daily_date_en_uses_new_york():
    now = datetime(2026, 10, 24, 3, 59, tzinfo=timezone.utc)  # 23:59 EDT on the 23rd
    assert c.daily_date("en", now) == "2026-10-23"
    assert c.daily_date("en", now.replace(hour=4, minute=0)) == "2026-10-24"


def test_daily_date_zh_uses_shanghai():
    now = datetime(2026, 10, 23, 15, 59, tzinfo=timezone.utc)  # 23:59 in Shanghai
    assert c.daily_date("zh", now) == "2026-10-23"
    assert c.daily_date("zh", now.replace(hour=16, minute=0)) == "2026-10-24"


# words: the API response is external input, so its shape is checked.

def test_words_returns_all_sixteen():
    assert len(c.words(puzzle(), "en", "2026-10-23")) == 16


@pytest.mark.parametrize("bad", [
    puzzle(date="2026-10-22"),
    puzzle(language="zh"),
    puzzle(groups=GROUPS[:3]),
    puzzle(groups=GROUPS[:3] + [{"words": ["A", "B", "C"]}]),
    puzzle(groups=GROUPS[:3] + [{"words": ["A", "B", "C", ""]}]),
    puzzle(groups=GROUPS[:3] + [{"words": ["A", "B", "C", 4]}]),
    puzzle(groups=GROUPS[:3] + [{"words": ["A", "B", "C", "X" * 41]}]),
    puzzle(groups=GROUPS[:3] + [{"words": ["MIRROR", "B", "C", "D"]}]),
    puzzle(groups="nope"),
    [],
])
def test_words_rejects_malformed(bad):
    with pytest.raises(ValueError):
        c.words(bad, "en", "2026-10-23")


# shuffle: stable for a given seed, so re-running the Action changes nothing.

def test_shuffle_is_a_stable_permutation():
    ws = c.words(puzzle(), "en", "2026-10-23")
    a = c.shuffle(ws, "en 2026-10-23")
    assert a == c.shuffle(ws, "en 2026-10-23")
    assert sorted(a) == sorted(ws)
    assert a != ws


def test_grid_is_four_rows_of_four_and_escapes_html():
    html = c.grid(["<b>", "&", *map(str, range(14))])
    assert html.count("<tr>") == 4 and html.count("<td>") == 16
    assert "&lt;b&gt;" in html and "&amp;" in html and "<b>" not in html


# replace_section: only the marked block changes; markers must be there once.

README = "top\n<!-- connections:start -->\nold\n<!-- connections:end -->\nbottom\n"


def test_replace_section_swaps_only_the_block():
    out = c.replace_section(README, "new")
    assert out == "top\n<!-- connections:start -->\nnew\n<!-- connections:end -->\nbottom\n"


@pytest.mark.parametrize("text", [
    "no markers here",
    README + README,
    "<!-- connections:end -->\n<!-- connections:start -->\n",
])
def test_replace_section_requires_one_ordered_pair(text):
    with pytest.raises(ValueError):
        c.replace_section(text, "new")


def test_section_has_both_grids_and_play_links():
    s = c.section(["A"] * 16, ["甲"] * 16)
    assert s.count("<table>") == 3  # the outer two-cell table and two grids
    assert s.count("https://connections.zhili.dev/") == 2
    assert "English" in s and "中文" in s
