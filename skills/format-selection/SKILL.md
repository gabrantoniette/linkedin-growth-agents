---
name: format-selection
description: Decide which format carries a post best on LinkedIn (PDF carousel, single image, short video or plain text) before designing anything, from what the post contains and the evidence in references/kb-visual-formats.md. Use it at the start of every design request.
---

# Format selection

Pick the format from the content, not from habit. `kb-visual-formats.md` §2
says what each format tends to do on each platform; this procedure decides
which one this particular post needs.

## Step 1: read what the post has

From the post (the section under `## Post (pt-BR)`), write down three things:

1. **Beats.** How many distinct ideas does the argument have, counted the way
   they would become slides: the hook, each piece of evidence, the closing.
2. **Proof assets.** What real, verifiable things exist: code the user wrote,
   output from a real run, a measured number stated in the post, a real system
   that can be drawn, a public page, a repository.
3. **Motion.** Is the proof something that only makes sense in time: a UI
   interaction, streaming output, a before and after?

## Step 2: decide

| When the post... | Format | Evidence |
|---|---|---|
| has 4 or more beats with sequence or structure: steps, a comparison, an architecture, a debugging story with evidence | **PDF carousel**, 1080x1350 | The document is the top engagement format in every LinkedIn dataset, and 12.92% of all saves (§2.1) |
| is carried by one real artifact: a screenshot, a code excerpt, one number | **Single image**, 1080x1350 | Portrait images beat square and landscape (§2.1) |
| is an argument or a story with no visual proof | **Text post**, 1,000+ characters | Long text beats short text; a visual with nothing to show is worse than none (§2.1, HONESTY) |
| has proof that is motion | **Short video**, 4:5 | Video reaches less than average on a personal profile, so only when motion is the proof (§2.1) |

Tie-breakers:

- **Carousel or image?** If the second slide would only restate the first, it
  is an image.
- **Carousel or text?** Fewer than four beats, or nothing real to put on the
  slides, is a text post.
- **Video or carousel?** If every frame reads as a still, it is a carousel.
- **The user named a format.** Do it, and say in one sentence if the evidence
  points elsewhere.

## Step 3: the gates that block any format

- The post has no `[PREENCHER` marker and its front matter is not
  `status: rejected`.
- Every number planned for a slide is stated in the post or in the user's data.
- Every screenshot planned can be captured from a real public page, and every
  code slide uses code or output that really exists.

If a gate fails, stop and say what is missing. Do not design around a gap: a
beautiful slide with an invented number is the worst possible outcome.

## Step 4: state the decision

One or two sentences, before building: the format, the number of slides or
scenes, the reason, and the section of the reference that supports it.

> Formato: carrossel de 7 slides. O post descreve uma arquitetura em quatro
> etapas e tem um trecho de código real, e documento é o formato de maior
> engajamento para perfil pessoal (kb-visual-formats.md §2.1).

## Cross-posting

Only when the user asks. The same PNG slides serve Instagram and Threads, and X
takes a thread; the `post-copy` skill has the adaptations.
