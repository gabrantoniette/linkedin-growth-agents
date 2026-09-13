"""The studio: turns a post into the asset that carries it.

Everything in this package is deterministic. No model is called from here: an
agent (the Post Designer) decides WHAT goes on each slide and writes it down as
a spec, and the studio decides HOW it looks, the same way every time. That
split is the point. A model is good at compressing an argument into eight
slides and bad at keeping a 40px margin identical on all of them; code is the
other way around.

The pieces, in the order a render walks through them:

- `themes`   the visual identity: palettes, fonts, and the contrast math
- `spec`     the contract a spec has to meet before anything is drawn
- `text`     inline markup and typography for slide text
- `lint`     the soft limits (words per slide, slide count) as warnings
- `html`     spec -> HTML, through the Jinja templates in `templates/`
- `browser`  the headless Chromium every render goes through, offline
- `carousel` HTML -> PDF, one PNG per slide, and the contact sheet
- `video`    the same slides, animated, encoded to MP4 with captions
- `capture`  screenshots of real web pages, with the safety checks
- `convert`  any supported file -> a PDF with the same page size

The evidence behind the numbers in here (slide size, type size, reading speed)
lives in `references/kb-visual-formats.md`. When a constant cites a section,
that is where to look before changing it.
"""
