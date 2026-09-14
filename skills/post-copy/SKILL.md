---
name: post-copy
description: Write the text that goes out with each format - the caption for a carousel, image or video, the LinkedIn document title, the first comment and alt text - and save it as media/<slug>/post.md with publishing steps. Also adapts the post for Instagram, X and Threads when asked. Use after the asset renders cleanly.
---

# Post copy by format

The asset is half of the post. The other half is text, and it has to work on
its own: search reads the caption, not the PDF, and a screen reader reads the
alt text, not the image.

## Start from the approved post

The Writer and the Editor already produced the text post. Adapt it for the
format; do not rewrite the argument, and never add a fact that is not in it.
The VOICE, WRITING and FORBIDDEN rules apply to every line here.

## Carousel caption (LinkedIn)

- The hook inside the first 140 characters (the mobile cut), making the same
  promise as the cover.
- Two to four short paragraphs: the context, and what the slides deliver. It is
  shorter than the text post, because the slides carry the evidence.
- The core claim in plain words: the PDF is not read as the post's text.
- The closing question, the same one as the closing slide.
- "Link no primeiro comentário" when there is a link, and zero to three
  specific hashtags at the end.

## Document title

At most 60 characters, descriptive and not clickbait: it sits at the top of the
document viewer. Usually the cover headline, shortened.

## Image post

A full caption, because the image does not carry the whole argument (posts over
1,000 characters perform better, kb-visual-formats.md §2.1), plus alt text of at
most 300 characters that says what is in the image and repeats any text in it
that carries meaning.

## Video

A caption like the carousel's, the `captions.srt` file uploaded with the video,
and a first line that does not depend on sound.

## First comment

The link or links, each with a few words saying what it is. Nothing else: no
"obrigado por ler", no request to follow.

## The file: media/<slug>/post.md

Save it with `save_artifact` before the final answer, with these headings:

```markdown
---
format: carousel
source_post: posts/2026-09-04-topic.md
slides: 8
---

## Legenda (pt-BR)

(the caption)

## Título do documento

(the title; carousel only)

## Primeiro comentário

(the links)

## Texto alternativo

(alt text; image posts, and one line per screenshot slide)

## Como publicar

1. LinkedIn: Começar publicação > Adicionar documento, e envie `content/media/<slug>/carousel.pdf`.
2. Título do documento: (the title).
3. Cole a legenda e publique.
4. Comente o link logo depois.
```

For an image post the first step uploads `image.png` through "Adicionar mídia";
for a video, `video.mp4` plus `captions.srt`.

When something is missing, such as the exact URL of a repository, write the
project's marker `[PREENCHER: what is missing]`, the same one the Writer uses,
and say it in the final answer. Never fill the gap with a guess, and never
invent a different marker: the other tools look for `[PREENCHER`.

**Never use the heading `## Post (pt-BR)` in this file.** That heading is what
`linkedin publish` sends as a text-only post, and a carousel caption published
without its PDF is a broken post.

## Cross-posting, only when the user asks

`references/cross-platform.md` has what changes on Instagram, X and Threads.
Add one section per platform to post.md (`## Instagram`, `## X`, `## Threads`).
The system publishes only to LinkedIn, and only text: everything else is a
draft for the user.
