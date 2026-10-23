# github.com/lzblack profile README.
# The typing header is drawn from outlined JetBrains Mono; re-run `make typing`
# whenever the card line changes (it must match zhili.me's card).

LINE := I teach. I build. I study both.
FONT := .cache/JetBrainsMono-Regular.ttf
FONT_URL := https://cdn.jsdelivr.net/gh/JetBrains/JetBrainsMono@v2.304/fonts/ttf/JetBrainsMono-Regular.ttf

.PHONY: test typing connections

test:
	uv run pytest -q

$(FONT):
	@mkdir -p .cache
	curl -sfL -o $@ $(FONT_URL)

typing: $(FONT)
	uv run python scripts/typing_svg.py $(FONT) assets/typing.svg "$(LINE)"
	uv run python scripts/typing_svg.py --dark $(FONT) assets/typing-dark.svg "$(LINE)"

# What the daily Action runs.
connections:
	uv run python -m scripts.connections README.md
