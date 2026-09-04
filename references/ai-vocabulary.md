# Vocabulary and tics that give away AI-generated text

Adapted from [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), the `linkedin-humanizer` and `linkedin-comment-drafter` skills. This file
spells out, with concrete examples, the **VOICE** criterion of the Editor's
rubric (`principles.py`, `RUBRIC`). Read it before reviewing a draft, not only
once you already suspect it.

**The banned words below stay in Portuguese.** The posts are written in
Portuguese, so the tell is the Portuguese word. Translating this list would
delete the only thing it is for.

## Hard rule: no em dash, no en dash

Never use `—` (em dash) or `–` (en dash), and never `--` as a substitute. It is
the single biggest tell of AI-generated text in 2026, more recognizable than any
word in the list below. Use a period, a comma, or split the sentence in two.

## Banned vocabulary

Never use these words and expressions:

- alavancar (in the sense of "use"), utilizar (instead of "usar"), facilitar,
  otimizar used vaguely, robusto, perfeito (in the sense of "integrated"),
  aprofundar-se, navegar (metaphorically), destravar, aproveitar, cultivar,
  fomentar
- fundamentalmente, essencialmente, em última análise, crucialmente,
  notavelmente
- cenário, ecossistema, paradigma, universo (metaphorically), jornada (outside
  its literal sense)
- "não se trata apenas de X, mas de Y"
- "no mundo acelerado de hoje" / "na era digital atual"
- "game changer", "mergulho profundo", "no fim das contas"

This replaces and extends the short list already in `DO_NOT` ("sinergia",
"disruptivo", "game changer", "mindset"). Keep both in mind; this one is simply
more detailed.

## Structure that sounds more human

- Paragraphs of one to three lines. Already a project rule.
- One sentence that stands on its own, out of context, as if screenshotted.
- At least one concrete number or proper noun per block of text.
- Never close with "o que vocês acham?". It is the signature of someone who did
  not know how to end.

## Patterns to avoid (a sign of AI, not just of cliché)

- Restating the post's own thesis in the closing ("no fim, isso mostra que...").
- Generic praise carrying no new information.
- Worn openers: "Isso.", "100%", "Não poderia concordar mais".
- A decorative rule of three ("mais rápido, mais barato, melhor") when the three
  items do not each carry real information.
- Too much passive voice. If more than one sentence in ten is passive, rewrite
  it active.
- Excessive symmetry: adjectives always in pairs, transitions that are too tidy,
  mirrored sentences. This is already in the Editor's `RUBRIC`; this list just
  gives concrete examples of what to look for.

## Before approving a draft, ask

Does the text introduce at least one concrete noun or concept that would not be
obvious without having lived the situation? If the answer is no, the text could
probably have been written by anyone from the documentation, and that already
fails the rubric's SPECIFICITY criterion.

## On automated AI detectors (GPTZero, Originality.ai, and the like)

Do not use them as an approval gate. They are publicly unreliable: OpenAI shut
down its own classifier in 2023 citing 26% accuracy, and third-party detectors
have documented bias against dense technical writing and against non-native
English speakers (Liang et al., 2023, *Patterns*). The criterion that counts is
the Editor's rubric, read by a human, not a score from an API.
