---
name: carousel-design
description: Build a PDF carousel (LinkedIn document post, also valid for Instagram and Threads) or a single-image post from a written post. Outline the deck one idea per slide, write the YAML spec for the studio's layouts, render it with render_carousel or render_image_post, and review the contact sheet until every slide reads at phone size.
---

# Carousel design

A carousel is the post's argument compressed into slides, one idea each, with
the evidence on the page. The studio decides how it looks; this procedure is
about what goes on each slide and in what order.

## 1. Outline before writing any YAML

Write the deck as a list of headlines, one per slide. Each headline is a full
sentence that states the point of that slide (the assertion-evidence structure,
kb-visual-formats.md §4). Then name the evidence each slide shows.

A typical deck has 6 to 10 slides:

1. **cover**: the hook, at most twelve words, making the same promise as the
   first line of the post;
2. **the tension**: why this matters, usually a `statement`;
3. **the evidence**, one idea per slide: code, a diagram, a comparison, a
   measured number, steps, a real screenshot;
4. **closing**: the question the post ends on, and where the link is.

Rules that hold for every slide:

- One idea per slide. Two ideas are two slides.
- At most about 45 words a reader has to read.
- Slide 2 also works as a hook: Instagram can show it first to someone who
  scrolled past the cover.
- Headlines are a full sentence. The phrase that carries the point goes
  `**heavy**`, and at most one phrase per slide goes under the `==marker==`
  (the highlighter). Never a single word marked for decoration.
- `numbered: true` only when the items are a sequence or a ranking.
- No em dash or en dash (the render refuses them), decimal comma, `R$ 47,32`.
- Every fact comes from the post or the user's data. No number, name, quote or
  output that is not there.

## 2. Choose a layout per slide

`references/layouts.md` lists every layout with its fields, limits and an
example. The quick map:

| The slide shows... | Layout |
|---|---|
| the hook | `cover` |
| one sentence that has to land | `statement` |
| two to six points that are not a sequence | `points` |
| a process, in order | `steps` |
| real code, or real terminal output (`frame: terminal`) | `code` |
| two options against the same criteria | `compare` |
| one measured number, with its source | `metric` |
| someone else's words, attributed | `quote` |
| a real screenshot | `image` |
| a flow between two to six parts | `diagram` |
| values that add up, or a list of measured values | `ledger` |
| the question the post ends on | `closing` |

**Theme.** `jornal`, always: newsprint, serif headlines, the evidence pasted on
torn paper, and a closing page printed in reverse. Two things follow the post:
the `masthead` (a two to four word label for the subject, and where it comes
from, such as the repository) and the `accent`, the highlighter's color:
`yellow` by default, `pink`, `green` or `blue` when the photo or the subject
asks for it, for example a yellow object that would vanish on yellow.
`drafting` and `blueprint` are the previous identity; use them only when the
request names them.

## 3. Find the photo

Every carousel and image post carries at least one real photo of its subject
(DESIGN rules). It illustrates; it never proves.

1. `search_photos` with the object or the scene the post is about, in English
   and concrete: 'black headphones', 'clothing rack', 'balance scale'. An idea
   ('recommendation', 'learning') finds nothing usable.
2. Look at the sheet. Prefer one object on a plain white background: it becomes
   a cutout. A vintage drawing or engraving also works well, as a print.
3. `get_photo(slug, photo_id, name, cutout=True)` for an object on white, or
   without `cutout` for anything else. Look at the cutout it returns.
4. Place it: on the cover, the `collage` takes one `capture` (a screenshot of
   the work), one `cutout` and one `print`; on any other slide, `photo` puts it
   in the top right corner, beside the headline. One photo per slide at most.

The credit goes into `photos/credits.json` on its own. Mention the photo in
`post.md` under "Fotos", with its source.

## 4. Write the spec

```yaml
title: "The document title, at most 60 characters"
language: pt-BR
theme: jornal
masthead:
  label: "Loja que aprende"
  detail: "products-recommendations"
accent: yellow
slides:
  - layout: cover
    headline: "Esta loja escolhe o que recomendar **sem nenhuma regra ==escrita à mão==**"
    collage:
      - image: media/<slug>/screens/<capture>.png
        kind: capture
      - image: media/<slug>/photos/<name>-recorte.png
        kind: cutout
  - layout: statement
    text: "..."
```

Do not add an `author` block: the name and tagline come from the profile.

## 5. Render and fix

Call `render_carousel(slug, spec)`, or `render_image_post(slug, spec)` for a
single slide.

- **NOT RENDERED** means no final file was written. Fix exactly what the report
  lists and call again. Overflow is fixed by cutting words or splitting the
  slide, never by asking for smaller type.
- **Warnings** do not block. Fix the ones about words per slide, a missing
  photo, two highlighted phrases and slide count unless there is a reason not
  to; "text shrunk to N%" means the slide is too dense.

## 6. Look at what you made

The render returns the contact sheet as an image. Look at it as the feed will
show it, then call `inspect_slides` on the cover and on the densest slide, and
go through `references/review-checklist.md`. Fix the spec and render again.

Stop after two review rounds past the first clean render. The spec is saved
next to the PDF, and the user can edit it and run `linkedin render`.

## 7. Single-image posts

The same spec with exactly one slide, rendered with `render_image_post`. The
layouts that work alone: `metric`, `code`, `image`, `statement`, `compare`,
`ledger`. The photo goes in the slide's `photo`.
