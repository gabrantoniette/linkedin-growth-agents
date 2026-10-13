# Layout reference

Every layout the studio renders, its fields and limits, and one example.

The examples use facts about this project itself, so they are true and anyone
can check them in the repository. In a real spec, every fact comes from the
post being designed and from the user's data, never from these examples.

**Inline marks**: `**strong**` (heavy type), `*emphasis*` (italic), `==marker==`
(the highlighter), and `` `code` ``. In a headline, `**...**` sets the phrase
that carries the point in heavy type and `==...==` runs the highlighter over it,
one highlighted phrase per slide at most. A line break (`\n`) inside a headline
is kept, to break the cover's hook where it reads best.

**On every slide**, optional: `note`, small print under the content (up to 160
characters): a caveat, a date, a source for the whole slide.

**On every slide but the cover, `metric` and `image`**, optional: `photo`, a
photo of the subject in the top right corner, beside the headline:

| field | required | limit |
|---|---|---|
| `image` | yes | a path from content/, saved by `get_photo` under `media/<slug>/photos/` |
| `kind` | no | `print` (black and white, taped on; the default) or `cutout` (the `-recorte.png`, over the highlighter) |
| `caption` | no | 80 characters, small print under the photo |
| `alt` | no | 300 characters |

**For the whole deck**, optional: `masthead`, the running head on every slide
(`label`, two to four words for the subject; `detail`, where it comes from, in
mono), and `accent`, the highlighter's color: `yellow` (default), `pink`,
`green` or `blue`.

**Video only**, optional on every scene: `duration` (seconds) and `narration`
(what is said during the scene; becomes captions).

---

## cover

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters; aim for 12 words or fewer |
| `subtitle` | no | 200 characters; aim for 22 words or fewer |
| `collage` | no | up to three pictures above the hook, one of each `kind`: `capture` (a screenshot of the work, pasted in the middle), `cutout` (an object on transparent ground, on the left over the highlighter), `print` (a photo, on the right, in black and white over a halftone). Each takes `image`, `kind` and `alt` |

```yaml
- layout: cover
  headline: "O Editor reprova um post inteiro **por um único ==critério==**."
  subtitle: "A rubrica tem sete critérios, e só um deles zera a nota."
  collage:
    - image: media/2026-09-13-exemplo/screens/rubrica.png
      kind: capture
      alt: "A rubrica do Editor, com os sete critérios"
    - image: media/2026-09-13-exemplo/photos/caneta-vermelha-recorte.png
      kind: cutout
      alt: "Uma caneta vermelha"
```

## statement

| field | required | limit |
|---|---|---|
| `text` | yes | 260 characters; aim for 25 words or fewer |
| `support` | no | 200 characters; aim for 20 words or fewer |
| `tally` | no | a receipt under the sentence: an optional `title`, one to five `rows` (`label` and `value`) and an optional `total`, for the items that make up the claim |

```yaml
- layout: statement
  text: "Verdade não entra ==na média==."
  support: "Se o critério VERDADE zera, a nota dos outros seis não importa: o post volta reprovado."
```

## points

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `items` | yes | 2 to 6 items; aim for 16 words or fewer each |
| `numbered` | no | `false` by default; `true` only for a sequence or a ranking |

```yaml
- layout: points
  headline: "O Editor corta três vícios de texto gerado antes de dar nota"
  items:
    - "Frases espelhadas, do tipo \"não é só X, é Y\""
    - "Adjetivos sempre em pares"
    - "Um parágrafo final que resume o próprio post"
```

## steps

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `steps` | yes | 2 to 5, each with `title` (aim for 8 words) and optional `detail` (18 words) |

```yaml
- layout: steps
  headline: "Um post passa por quatro etapas antes de virar arquivo"
  steps:
    - title: Researcher
      detail: "junta material sobre o tema já decidido"
    - title: Writer
      detail: "escreve a versão em português e a em inglês"
    - title: Editor
      detail: "aplica a rubrica de sete critérios e corta"
    - title: record_post
      detail: "confere que o arquivo existe no disco"
```

## code

| field | required | limit |
|---|---|---|
| `headline` | no | 140 characters |
| `code` | yes | aim for 14 lines and 56 columns or fewer |
| `language` | no | a Pygments name: `python`, `typescript`, `sql`, `console`; guessed from `filename` |
| `filename` | no | printed under the listing |
| `frame` | no | `listing` (line numbers) or `terminal` (a shell session, prompts marked) |
| `highlight` | no | 1-based line numbers, three at most |
| `caption` | no | 200 characters |

Secrets in the code are masked before drawing, and the report says what was
masked. Code on a slide is real code from the user's work, never written for
the slide.

In the jornal theme the listing is printed on a torn piece of computation
paper, without line numbers, and the highlighted lines go under the
highlighter.

```yaml
- layout: code
  headline: "A API do LinkedIn exige escapar **quinze caracteres** no texto"
  photo:
    image: media/2026-09-13-exemplo/photos/maquina-de-escrever.jpg
    kind: print
    caption: "Máquina de escrever"
  filename: tools/linkedin.py
  language: python
  highlight: [1]
  code: |
    LITTLE_RESERVED = set(r"\|{}@[]()<>#*_~")

    def escape_little(text: str) -> str:
        return "".join("\\" + c if c in LITTLE_RESERVED else c for c in text)
  caption: "Parênteses incluídos, e texto escrito por IA tem parêntese em toda frase."
```

## compare

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `left`, `right` | yes | each a `title` (40 characters) and 1 to 5 `items` (aim for 10 words each) |
| `favored` | no | `left`, `right` or `none`: the side the post argues for |
| `verdict` | no | 200 characters |

```yaml
- layout: compare
  headline: "Workflow quando a ordem é conhecida, Team quando não é"
  left:
    title: Team
    items:
      - "O líder decide quem responde"
      - "Gasta tokens decidindo"
      - "Serve para conversar"
  right:
    title: Workflow
    items:
      - "A ordem está escrita no código"
      - "Não gasta tokens decidindo"
      - "Serve para produzir"
  favored: none
  verdict: "Os dois convivem: `linkedin chat` usa o Team e `linkedin post` usa o Workflow."
```

## metric

| field | required | limit |
|---|---|---|
| `value` | yes | 14 characters, as written: `100`, `96%`, `R$ 47,32` |
| `unit` | no | 24 characters, printed on the dimension line above the value |
| `label` | yes | 120 characters; aim for 12 words |
| `detail` | no | 200 characters |
| `source` | yes | where the number comes from, 3 to 140 characters |

The source is required on purpose: a number on a slide is a claim.

```yaml
- layout: metric
  value: "60"
  unit: dias
  label: "é quanto dura o token de publicação do LinkedIn"
  detail: "A renovação automática só existe para parceiros aprovados. Depois disso, gera-se outro."
  source: "README do projeto, seção Connecting LinkedIn"
```

## quote

| field | required | limit |
|---|---|---|
| `quote` | yes | 320 characters, exactly as the person wrote or said it |
| `author` | yes | 80 characters |
| `source` | no | where it was said, 140 characters |

```yaml
- layout: quote
  quote: "Measure. Don't tune for speed until you've measured, and even then don't unless one part of the code overwhelms the rest."
  author: Rob Pike
  source: "Notes on Programming in C, 1989"
```

## image

| field | required | limit |
|---|---|---|
| `headline` | no | 140 characters |
| `image` | yes | path from content/, usually `media/<slug>/screens/<name>.png` |
| `frame` | no | `browser` prints the page address above the capture; `plain` shows the image alone |
| `url` | no | the real address, shown by the browser frame |
| `fit` | no | `cover` (fill, cropped from the top) or `contain` (whole image) |
| `caption` | no | 200 characters |
| `source` | no | 140 characters |
| `alt` | no, but always write it | what the image shows, up to 300 characters |
| `mark` | no | a box drawn by hand around the proof: `box: [left, top, right, bottom]` in the capture's own pixels, and an optional `label` of six words at most. Needs `fit: contain` |
| `tone` | no | `auto` (black and white in the jornal theme), `mono` or `color`; `color` when the color is the evidence |

```yaml
- layout: image
  headline: "O framework por baixo dos agentes **é open source**"
  image: media/2026-09-13-exemplo/screens/agno-repo.png
  frame: browser
  url: https://github.com/agno-agi/agno
  fit: contain
  mark:
    box: [40, 120, 620, 210]
    label: "a descrição do projeto"
  alt: "Página do repositório agno-agi/agno no GitHub, com a lista de arquivos e a descrição do projeto"
  source: github.com/agno-agi/agno
```

## diagram

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `nodes` | yes | 2 to 6, each a `label` (aim for 4 words), an optional `detail` (10 words) and `key: true` on the one node the post is about (printed in reverse; one at most) |
| `caption` | no | 200 characters |

The nodes are drawn in order, top to bottom, with arrows between them: use it
for flows and pipelines, not for hierarchies.

```yaml
- layout: diagram
  headline: "O caminho de um post **até o feed**"
  nodes:
    - label: linkedin post
      detail: "Researcher, Writer e Editor"
    - label: content/posts/
      detail: "o arquivo com as versões pt-BR e en"
    - label: linkedin publish
      detail: "extrai só a seção pedida"
      key: true
    - label: API do LinkedIn
      detail: "POST /rest/posts"
  caption: "Nada chega ao feed sem uma confirmação explícita."
```

## ledger

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `rows` | yes | 2 to 6, each a `value` (24 characters, as written: `4`, `14.337`, `R$ 47,32`) and a `label` (aim for 10 words) |
| `total` | no | a `value` and a `label` under a double rule; only when the rows add up to it |
| `source` | no | where the values come from, 140 characters |

A breakdown, values first, the way a reader scans it. Use it when the parts
add up to a whole the post talks about, or for a short list of measured values.

```yaml
- layout: ledger
  headline: "A rubrica do Editor tem ==sete critérios=="
  rows:
    - value: "1"
      label: "zera a nota sozinho: VERDADE"
    - value: "6"
      label: "entram na média"
  total:
    value: "7"
    label: "critérios por post"
```

## closing

| field | required | limit |
|---|---|---|
| `headline` | yes | 140 characters |
| `question` | no, but almost always | the post's closing question, 220 characters |
| `cta` | no | where the link is, 90 characters; never "comente X" or "salve este post" |

In the jornal theme the closing page is printed in reverse, dark, and the
`cta` becomes a red tag.

```yaml
- layout: closing
  headline: "Sete critérios, e ==nenhum deles é curtida.=="
  question: "Quem aqui já reprovou um texto próprio por um critério que zera tudo? Qual era o critério?"
  cta: "A rubrica completa está no primeiro comentário."
```
