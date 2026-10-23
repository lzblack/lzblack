"""Self-made typing-header SVG for the GitHub README.

Glyphs are outlined JetBrains Mono paths (no <text>, no web fonts: GitHub serves
README images through camo with external resources blocked). Animation is SMIL
with discrete steps, which renders inside <img> in all major browsers.
Usage: typing_svg.py [--dark] FONT.ttf OUT.svg "line one" "line two" ...
With a single line it types once and stays, with the cursor blinking.
--dark draws light text for dark backgrounds. The README picks the variant with
<picture>, which follows the viewer's GitHub theme (an in-SVG media query would
follow the OS instead).
"""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

SIZE = 20                  # px
H, BASE = 40, 27           # canvas height, baseline
TYPE, ERASE = 0.065, 0.025 # seconds per character
HOLD, GAP = 1.8, 0.35      # pause on a full line, pause on an empty one

args = sys.argv[1:]
DARK_THEME = args[:1] == ["--dark"]
font_path, out, *lines = args[1:] if DARK_THEME else args
font = TTFont(font_path)
gs, cmap = font.getGlyphSet(), font.getBestCmap()
upm = font["head"].unitsPerEm
s = SIZE / upm
adv = gs[cmap[ord("a")]].width * s   # monospace advance in px

def glyph(ch):
    pen = SVGPathPen(gs)
    gs[cmap[ord(ch)]].draw(pen)
    return pen.getCommands()

paths = {ch: glyph(ch) for ch in set("".join(lines)) if ch != " "}

# Timeline: each line types in, holds, erases, then the next one starts.
t, spans = 0.0, []
for ln in lines:
    n = len(ln)
    frames = [(t + k * TYPE, k) for k in range(1, n + 1)]
    t_full = t + n * TYPE
    if len(lines) == 1:
        spans.append(frames); t = t_full; break
    frames += [(t_full + HOLD + k * ERASE, n - k) for k in range(1, n + 1)]
    t = t_full + HOLD + n * ERASE + GAP
    spans.append(frames)
T = t

ONCE = len(lines) == 1
REPEAT = 'fill="freeze"' if ONCE else 'repeatCount="indefinite"'

def anim(attr, frames, start):
    """Discrete SMIL animation over the whole cycle; frames = [(time, value)]."""
    pts = [(0.0, start)] + [(ft / T, v) for ft, v in frames if ft < T or (ONCE and ft <= T)]
    kt = ";".join(f"{k:.5f}" for k, _ in pts)
    vs = ";".join(f"{v:.1f}" for _, v in pts)
    return f'<animate attributeName="{attr}" dur="{T:.3f}s" {REPEAT} calcMode="discrete" keyTimes="{kt}" values="{vs}"/>'

W = int(max(len(l) for l in lines) * adv + 16)
parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">',
         f'<title>{" / ".join(lines)}</title>',
         ('<style>.t{fill:#E6EDF3}.c{fill:#8EA2FF}</style>' if DARK_THEME else '<style>.t{fill:#16181D}.c{fill:#1F3FBF}</style>'),
         "<defs>"]
for i, frames in enumerate(spans):
    parts.append(f'<clipPath id="c{i}"><rect x="0" y="0" height="{H}" width="0">'
                 + anim("width", [(ft, k * adv) for ft, k in frames], 0) + "</rect></clipPath>")
parts.append("</defs>")
for i, ln in enumerate(lines):
    gl = "".join(f'<path transform="translate({j * adv:.2f} {BASE}) scale({s} {-s})" d="{paths[ch]}"/>'
                 for j, ch in enumerate(ln) if ch != " ")
    parts.append(f'<g class="t" clip-path="url(#c{i})">{gl}</g>')
cur = sorted((ft, k * adv) for frames in spans for ft, k in frames)
parts.append(f'<rect class="c" y="{BASE - SIZE * 0.78:.1f}" width="2" height="{SIZE * 0.95:.1f}" x="0">'
             + anim("x", cur, 0)
             + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect>')
parts.append("</svg>")
open(out, "w").write("".join(parts))
print(f"{out}: {W}x{H}, cycle {T:.1f}s")
