---
name: proof-screenshots
description: Capture real screenshots of public web pages (docs, repositories, release notes, papers) as proof for a slide, safely and legibly. Crop to what proves the point, capture narrow so the text reads on a phone, credit the source, never capture private pages or LinkedIn, and never fabricate output. Use whenever a slide needs a screenshot.
---

# Proof screenshots

A screenshot on a slide is evidence, so it has to be a real capture of a real
page, it has to show the part that proves the point, and the reader has to be
able to read it on a phone.

## What counts

- **A public page the post talks about**: a repository, a README, a docs page,
  a release note, a paper's abstract, a benchmark table.
- **The user's own code or terminal output** is not a screenshot: it is a `code`
  slide with the real text. Sharper, selectable in the PDF, and secrets are
  masked automatically.
- **Never**: a page behind a login, an internal dashboard, a client's system,
  anything confidential from the user's job, LinkedIn itself (the tool refuses
  it), or output that did not come from a real run.

## Screenshot or quote?

Decide before capturing. When the proof is **one sentence** of documentation or
of an article, a `quote` slide with the exact words and the page as `source`
beats a screenshot of the paragraph: it is legible, searchable and says the
same thing. A screenshot earns its place when **the eye has to see the thing
itself**: an interface, a chart, a repository page, a table of results, the
shape of a release note.

## Legibility decides the capture

A slide shows a capture about 864px wide. A page captured in a 1280px window
therefore shrinks to two thirds, and its 16px body text ends up near 11px on
the slide and around 4px in the hand. Nobody reads that.

- For a page of text, capture a **narrow window**: `width` between 600 and 720.
  The text is then drawn larger relative to the frame.
- Capture **the element** that holds the passage with `selector` (the section,
  `article`, `main`, a `table`), not a region of the page that happens to
  contain it.
- Crop to **whole blocks**. A line cut in half at the edge of the capture looks
  careless and reads as hiding something.
- Look at the image the tool returns. If you cannot read the passage at a
  glance, neither can the reader.
- **Two attempts at most.** If the passage is still small or cut after the
  second, switch to a `quote` slide.

## Capture

`capture_screenshot(slug, url, name, ...)`:

- `width` and `height`: the browser window. Narrow for text, as above; the
  default 1280x800 suits a repository page or an interface.
- `full_page` only when the length is the point. It is capped at 6000px.
- `dark_mode` when the deck uses the `blueprint` theme and the site has a dark
  theme.
- `hide`: CSS selectors for cookie banners or popups that cover the content.

Every capture writes a JSON file next to the PNG with the URL asked for, the
URL that loaded, the page title and the time. That is the image's provenance.

## Put it on a slide

```yaml
- layout: image
  headline: "The sentence the capture proves"
  image: media/<slug>/screens/<name>.png
  frame: browser            # prints the address above the capture
  url: https://example.org/the/real/page
  fit: contain              # the frame takes the capture's proportions
  alt: "What the image shows, including any text that matters, at most 300 characters"
  source: "the name of the site or the page"
```

Use `fit: cover` only for a capture taller than the space it gets, when showing
its top is enough (a repository page, a long article's opening).

## Rules

- The link goes in the first comment, never in the post body.
- The source is credited on the slide.
- If the page shows someone else's personal data, choose another page or crop
  it out with `selector`.
- Do not edit a capture, stitch captures into something that never existed, or
  put a capture next to a claim it does not support.
