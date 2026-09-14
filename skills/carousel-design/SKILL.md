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
- Headlines are stated plainly. No `**bold**`, `*emphasis*` or `==marker==`
  inside a headline; marks belong to body text, one per slide at most.
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
| the question the post ends on | `closing` |

**Theme.** `drafting` (computation paper) for most posts. `blueprint` when the
evidence is dark: terminal output, dark-mode screenshots. Never switch themes
for variety: the identity is what makes the series recognizable.

## 3. Write the spec

```yaml
title: "O título do documento, até 60 caracteres"
language: pt-BR
theme: drafting
slides:
  - layout: cover
    headline: "..."
  - layout: statement
    text: "..."
```

Do not add an `author` block: the name and tagline come from the profile.

## 4. Render and fix

Call `render_carousel(slug, spec)`, or `render_image_post(slug, spec)` for a
single slide.

- **NOT RENDERED** means no final file was written. Fix exactly what the report
  lists and call again. Overflow is fixed by cutting words or splitting the
  slide, never by asking for smaller type.
- **Warnings** do not block. Fix the ones about words per slide, emphasis in a
  headline and slide count unless there is a reason not to; "text shrunk to N%"
  means the slide is too dense.

## 5. Look at what you made

The render returns the contact sheet as an image. Look at it as the feed will
show it, then call `inspect_slides` on the cover and on the densest slide, and
go through `references/review-checklist.md`. Fix the spec and render again.

Stop after two review rounds past the first clean render. The spec is saved
next to the PDF, and the user can edit it and run `linkedin render`.

## 6. Single-image posts

The same spec with exactly one slide, rendered with `render_image_post`. The
layouts that work alone: `metric`, `code`, `image`, `statement`, `compare`.
