---
id: kb-visual-formats
title: "Reference base: visual formats on LinkedIn, Instagram, X and Threads"
version: 1.0
compiled: 2026-09-13
revalidate_by: 2026-12-13
language: en (slide copy examples stay in pt-BR)
scope:
  - format_choice
  - carousel_anatomy
  - page_separation
  - typography_and_legibility
  - color_and_identity
  - images_screenshots_code
  - video_and_captions
  - post_copy_by_format
  - cross_platform_adaptation
out_of_scope:
  - timing_and_frequency      # kb-linkedin-publicacao.md
  - hook_formulas             # hooks.md
  - paid_ads
global_confidence: medium
evidence_nature: observational (platform datasets) + experimental (learning and marketing research)
controlled_experiment_on_linkedin: false
---

# Reference base: visual formats

What each format does on each platform, how a carousel, an image and a video
should be built so they are read on a phone, and what the evidence behind every
number is. Written for the Post Designer, readable by anyone deciding a format.

---

## 0. Rules for the agent using this document

1. **HONESTY outranks any format gain.** A carousel with invented proof is worse
   than a plain text post with real proof. Nothing here licenses a fabricated
   screenshot, number, chart or quote.
2. **Say which population a number comes from.** Personal profiles, company
   pages and "creators" behave differently, and most studies measure only one
   of them. The user posts as a person: prefer `authoredup-3m-2026` and
   `vanderblom-2026` when they disagree with page-only data.
3. **Engagement rate is not one metric.** Buffer divides by reach, Socialinsider
   by impressions, Instagram benchmarks often by followers. Never compare two
   percentages from different sources as if they were the same measure.
4. **Research on learning and marketing justifies principles, not multipliers.**
   Mayer, Garner and Alley, Li and Xie, Kanuri et al. explain why one idea per
   slide and high contrast work. None of them measured LinkedIn.
5. **The user's own metrics win.** When `content/metrics.csv` has data, it is
   the authority and this file is the starting hypothesis.
6. **Cite the `source_id` (§11) when you state a number.**
7. **Precedence with the other references.** For days, times, frequency and the
   decision hierarchy, `kb-linkedin-publicacao.md` rules. For the per-post text
   checklist, `linkedin-algorithm.md`. This file rules format and design.

---

## 1. Canonical parameters

```json
{
  "format_priority_linkedin_personal_profile": [
    "document_carousel",
    "image_portrait",
    "text_long",
    "video"
  ],
  "carousel": {
    "size_px": [1080, 1350],
    "aspect": "4:5",
    "slides_typical": [6, 10],
    "slides_warn_above": 12,
    "linkedin_max_pages": 300,
    "linkedin_max_mb": 100,
    "instagram_max_slides": 20,
    "uniform_page_size_required": true,
    "document_title_required": true,
    "document_title_max_chars_recommended": 60,
    "confidence": "high for specs, low for slide count"
  },
  "type_px_on_1080_canvas": {
    "cover_headline": [72, 120],
    "slide_headline": [56, 80],
    "body_min": 34,
    "small_print_min": 22,
    "confidence": "medium"
  },
  "contrast_min": {"text": 4.5, "large_text": 3.0, "source": "WCAG 2.2 §1.4.3"},
  "words": {"cover_headline_max": 12, "per_slide_max": 45, "confidence": "low"},
  "image_post": {
    "size_px": [1080, 1350],
    "linkedin_alt_text_max_chars": 300,
    "linkedin_multi_image_max": 20
  },
  "video": {
    "feed_size_px": [1080, 1350],
    "vertical_size_px": [1080, 1920],
    "container": "MP4, H.264 video, AAC audio",
    "linkedin_length_s": [3, 900],
    "linkedin_max_gb": 5,
    "linkedin_caption_file": "SRT",
    "hook_window_s": 3,
    "caption_max_chars_per_second": 17,
    "caption_max_chars_per_line": 42,
    "caption_max_lines": 2,
    "caption_event_s": [0.833, 7],
    "safe_zone_9x16": {"top": 0.14, "bottom": 0.35, "sides": 0.06}
  },
  "text_post": {
    "linkedin_max_chars": 3000,
    "see_more_cutoff_mobile_chars": 140,
    "see_more_cutoff_desktop_chars": 210
  },
  "x": {"media_per_post_max": 4, "long_post_chars_premium": 25000, "single_image_px": [1200, 675]},
  "threads": {"post_chars": 500, "text_attachment_chars": 10000, "carousel_max_items": 20, "video_max_s": 300}
}
```

---

## 2. Format choice: what the data says, platform by platform

### 2.1 LinkedIn

| Source | Population | Metric | Document / carousel | Multi-image | Image | Video | Text | Link |
|---|---|---|---|---|---|---|---|---|
| `authoredup-3m-2026` | Personal profiles, 3M+ posts | Multiplier vs the profile's own median (reach / engagement) | **1.39x / 1.30x** | n/a | 1.20x / 1.33x | 0.86x / 0.93x | 1.07x / 0.78x | n/a |
| `buffer-engagement-2026` | Mixed accounts, 52M+ posts, all platforms | Median engagement rate, by reach | **21.77%** | n/a | 6.52% | 7.35% | 3.18% | 3.81% |
| `socialinsider-li-2026` | 16,645 business pages, 1.3M posts | Average engagement rate, by impressions | **7.00%** | 6.45% | 5.30% | 6.00% | 4.50% | 3.25% |
| `metricool-li-2026` | 63,108 accounts, pages and personal | Relative ranking | Carousels and multi-image ahead | ahead | behind | "underperforms" | n/a | n/a |

**Consensus, `confidence: high`:** the document (carousel) is the top format for
engagement on LinkedIn in every dataset. AuthoredUp adds the detail that matters
most for a personal brand: documents are 4.88% of posts but **12.92% of all
saved posts**, about 2.6 times their share, and only 4.88% of profiles post them
regularly. Saves are the long-half-life signal `kb-linkedin-publicacao.md` §6.3
describes.

**Divergence to preserve, video, `confidence: low`:** pages and mixed accounts
(Socialinsider, Buffer) put video above images. Personal profiles (AuthoredUp)
put it below their own average, with reach down 36% year over year;
`vanderblom-2026` calls video declining and recommends it only to creators who
enjoy the medium; Metricool says it underperforms in 2026. **For this user, a
personal profile, video is not the default format.**

Details worth using:

- **Portrait images win:** 1080x1350 at 2.83% median engagement, square 2.54%,
  landscape 2.14% (`authoredup-3m-2026`).
- **Long text beats short text:** 1,000+ characters get 1.18x reach and
  engagement; under 300 characters get 0.88x reach (`authoredup-3m-2026`).
- **Visuals are close to mandatory:** only the top 5% of creators succeed with
  text-only posts; the other 99% need a visual element (`vanderblom-2026`).
- **Carousel spread is wide:** strong carousels pass 41% engagement and weak ones
  sit near 5.4% (`buffer-engagement-2026`). The format does not rescue weak
  content; it amplifies what is there.

**Decision rule derived:** document carousel when the content has sequence or
structure (steps, a comparison, an architecture, a debugging story with
evidence); a portrait image when one real artifact carries the post; a long text
post when it is an argument or a story with no visual proof; video only when
motion is the proof (a real demo, a terminal run) or the asset is going to
Reels or Threads as well.

### 2.2 Instagram

| Source | Metric | Carousel | Single image | Reels |
|---|---|---|---|---|
| `buffer-engagement-2026` | Median engagement rate, by reach | **6.90%** | 4.44% | 3.31% |
| `socialinsider-ig-2026` | Engagement rate by followers, Q2 2026 | **0.50%** | 0.33% | 0.48% |

- Reels win **reach**: 36% more than carousels (`buffer-engagement-2026`), an
  average reach rate of 30.81%, two to three times the carousel's
  (`socialinsider-ig-2026`). Carousels win **engagement per impression** (+12%,
  Buffer) and saves: nine times more saves than a single image
  (`metricool-ig-2026`). `confidence: medium`.
- The profile grid previews posts at **3:4** since January 2025
  (`instagram-grid-2025`). A 1080x1350 upload shows at about 1013x1350 in the
  grid, trimmed at the sides: keep text away from the outer 40px.
- A carousel holds up to **20** slides.
- A carousel someone scrolled past can be shown again starting from another
  slide, usually the second. Widely reported by practitioners, not documented by
  Instagram. `confidence: low`. Cheap to design for: slide 2 should stand on its
  own as a second hook.

### 2.3 X

- Text leads: median engagement 3.56% for text, 3.40% images, 2.96% video, 2.25%
  links (`buffer-engagement-2026`). The Premium versus free divide moves the
  numbers more than format does. `confidence: medium`.
- Up to **4** media items per post; long posts up to **25,000** characters for
  Premium (`x-help-2026`).
- A single 16:9 image (1200x675) shows uncropped; multi-image posts are cropped
  from the center, so the essential content goes in the central 60 to 70%
  (`x-specs-2026`).
- **Adaptation:** a carousel becomes a thread, one slide's idea per post, with at
  most four of the slide PNGs attached where they are the evidence.

### 2.4 Threads

- Threads posts reach a 6.25% median engagement rate against X's 3.6%, and
  replying to comments adds 42% engagement (`buffer-threads-vs-x`).
- Visuals beat text even there: video 5.55%, images 4.55%, text 2.79%, links
  2.34% (`buffer-engagement-2026`).
- A post holds **500** characters; since September 2025 a **text attachment**
  holds up to **10,000** characters with formatting. Meta built it because people
  were posting screenshots of long text (`threads-attachments-2025`).
- Carousels up to **20** items, 4:5 recommended, video up to 5 minutes
  (`threads-specs-2026`).

### 2.5 What transfers across all four

1. **4:5 portrait is the common denominator** of the mobile feed. One set of
   1080x1350 slides serves LinkedIn, Instagram and Threads.
2. **Multi-frame formats win engagement and saves** on LinkedIn and Instagram.
3. **Video wins reach where the platform is built around it** (Reels), not on a
   LinkedIn personal profile in 2026.
4. **The feed is read on a phone, often muted.** Every asset has to work at a
   third of its size and without sound.
5. **Screenshots of text are native behaviour and inaccessible by default**: pair
   every one with alt text, or use the platform's text feature.

---

## 3. Carousel anatomy

### 3.1 Specifications (`linkedin-help-documents`)

- File types PDF, PPT, PPTX, DOC, DOCX. **PDF** is the only one that renders the
  same everywhere, so the studio always exports PDF.
- At most **100MB** and **300 pages**.
- **Every page the same size**: "PDFs with multiple sized pages must be fit to
  the same page size". Layers must be flattened.
- A **title is required** at upload and shows at the top of the viewer.
- Animations in the document show as static images. Links inside the PDF must be
  secure (https).
- Viewers can **download the document as a PDF** for accessibility, so the text
  in it must be real text, not a picture of text. The studio's PDFs are.
- The document cannot be edited after posting; only the caption can.

### 3.2 How many slides, `confidence: low`

No primary dataset with a published method settles slide count. Practitioner
guides converge on **5 to 10** (some say 8 to 12 for educational content), and
several claim engagement drops past slide 10 without showing data. The rule:
**as many slides as the argument has beats, one beat per slide**, with a warning
past 12.

### 3.3 The sequence

1. **Cover**: the hook. It is the thumbnail in the feed.
2. **Tension or context**: why this matters, in one sentence. On Instagram, this
   is also the possible second cover (§2.2).
3. **Evidence**, one slide per idea: the code, the diagram, the number, the
   comparison, the real screenshot.
4. **Synthesis**, optional: what it adds up to, never a recap of every slide.
5. **Closing**: the same concrete question the post ends on, and where the link
   is (the first comment).

### 3.4 The cover

- One hook of at most **twelve words**, large, high contrast, nothing competing
  with it. The formulas in `hooks.md` apply; the cover and the post's first line
  must make the same promise.
- A kicker label (the pillar, or the subject) orients without adding words.
- Instagram practitioners note the cover has to stand out in a grid of
  competing thumbnails; the same holds for the LinkedIn feed.

### 3.5 The closing slide

- A specific question worth answering (`principles.WRITING_RULES`), never
  "o que vocês acham?".
- Where the link is. Never "comente X", "marque alguém" or "salve para depois":
  asking for engagement is forbidden (`principles.DO_NOT`) and suppressed by the
  ranker (`linkedin-algorithm.md`).
- The identity footer is on every slide, so a slide reshared alone still points
  back to the profile.

---

## 4. Separating pages: one idea per slide

This is the part with experimental evidence, and it is what decides where one
slide ends and the next begins.

- **Coherence principle** (`mayer-multimedia`): people learn more deeply when
  extraneous material is excluded. Supported in 23 of 23 experimental tests,
  median effect size d = 0.86. On a slide: no decorative image, no filler
  sentence, no logo parade.
- **Signaling principle** (`mayer-multimedia`): cues that highlight the
  organization of the essential material help, with small to large effects. On a
  slide: one highlighted phrase, a numbered sequence, a kicker label.
- **Segmenting principle** (`mayer-multimedia`): complex material in
  learner-paced segments beats one continuous unit. A carousel is learner-paced
  by construction: the reader swipes when ready.
- **Assertion-evidence structure** (`garner-alley-2013`): 110 engineering
  students; slides with a **sentence headline stating the assertion** and
  **visual evidence** in the body produced better comprehension, fewer
  misconceptions, lower perceived cognitive load and better delayed recall than
  topic headlines with bullet lists. `confidence: high` for comprehension, not
  measured on engagement.
- **Text overlay on images** (`dang-2026-jmr`): posts that emphasize overlay text
  over pictorial content get fewer likes and comments; text-oriented posts do
  better when the text is centered, informative, positive and congruent with the
  picture, and when the picture has fewer prominent objects.
  `confidence: medium` (marketer-generated content, not personal profiles).
- **Mobile reading** (`nngroup-mobile`): comprehension on a phone matches a
  desktop for simple content, but reading slows down for difficult text. The
  complex part of an argument belongs in the structure of the deck, not in a
  dense paragraph on one slide.

**Rules derived:**

- Every slide's headline is a full sentence stating its point. "Contexto",
  "Resultados" and "Conclusão" are labels, not headlines.
- The body is evidence: code, a diagram, a number, a comparison, a screenshot.
- At most about 45 words a reader has to read on one slide.
- One signal per slide: one highlighted phrase or one accent word.
- If a slide needs a second idea, it is two slides.

---

## 5. Typography and legibility

- **Sizes on a 1080px canvas**, `confidence: medium`. Practitioner guides
  converge on headlines of 60 to 96px (covers up to about 120), body of 32 to
  40px, and never under about 28 to 32px (`carousel-typography-guides`). The
  physics agree: a phone shows the canvas at about a third of its size, so 36px
  lands near 12px in the hand. **Test: zoom the slide to 33%; if it is hard to
  read there, it is hard to read in the feed.**
- **Contrast**: WCAG 2.2 §1.4.3 asks 4.5:1 for normal text and 3:1 for large
  text (`wcag-22`). Contrast matters more than size: dark gray at 36px on a
  medium gray loses to black at 28px on white.
- **Faces**: one family for everything that is language, a monospace only for
  what is machine text (code, output, paths, URLs). Two families on a slide is
  the ceiling. The 2026 trend reports clean sans-serifs dominating
  (`instagram-design-trends-2026`), which is exactly why the default choice
  (Inter, a mono for labels, one italic serif word for emphasis) reads as a
  template: the studio uses Archivo, condensed for headlines and normal width
  for body, and IBM Plex Mono only for code.
- **Emphasis in headlines**: none. One accented word in a headline (in italic,
  in bold or in another color) is the most recognizable mark of a generated
  slide. The headline states the point; the evidence carries the emphasis.
- **Capitals**: not for labels, not for sentences. A sentence in capitals reads
  slower and shouts, and tracked capital labels over every heading are template
  chrome.
- **Unicode "bold" and "italic" in post text: never.** Screen readers announce
  them as mathematical symbols or skip them, and LinkedIn search does not index
  them (`unicode-bold-a11y`). Bold belongs on the slide, where it is real type.
- **Emoji**: at most two in the post (`principles.VOICE_RULES`), none on slides.
- **Wrapping**: balanced lines in headlines, no hyphenation, no one-word last
  line.

---

## 6. Video

### 6.1 Specifications

- **LinkedIn** (`linkedin-video-specs`): MP4 with H.264 video and AAC audio; 3
  seconds to 15 minutes on desktop; up to 5GB; aspect ratios from 1:2.4 to 2.4:1;
  an **SRT caption file** can be uploaded with the video.
- **Threads**: up to 5 minutes. **X**: long uploads for Premium.
- **Safe zones for 9:16**: Meta unified Stories, Reels and Feed into one safe
  zone in March 2026: keep the **top 14%, bottom 35% and 6% at each side** free of
  anything that must be read (`meta-safe-zones-2026`). `confidence: medium`,
  reported by several ad-spec guides.

### 6.2 The first seconds

- 47% of a video campaign's value is delivered in the first three seconds, and
  74% of the impact within ten (`facebook-iq-2016`, Facebook and Nielsen, ads).
  `confidence: medium` for organic feed video. **Rule: the claim is on screen in
  the first frame, not after an intro.**

### 6.3 Sound off and captions

- 69% of consumers watch video with the sound off in public places and 25% in
  private ones; 80% are more likely to finish a video that has captions
  (`verizon-publicis-2019`).
- Captioned video ads increase view time by 12% on average (`meta-captions`).
- The famous "85% of video is watched without sound" comes from publishers
  quoted by Digiday in 2016 about Facebook, never from platform data
  (`digiday-2016`). **Do not cite it as a LinkedIn number.** Figures like "79%"
  or "91% of LinkedIn video is watched muted" circulate without a traceable
  primary source: do not cite them either.
- **Caption timing** (`netflix-timed-text`): at most 42 characters per line and 2
  lines per event; each event on screen between 5/6 of a second and 7 seconds;
  reading speed capped at 17 characters per second for adult content in most
  Latin-script languages (20 for English). The studio uses 17 for Portuguese.

### 6.4 Length, `confidence: low`

The sources disagree: pages do best at 120 to 180 seconds
(`socialinsider-li-2026`); personal profiles see 3+ minute videos at 1.21x reach
and 0 to 30 second ones at 0.96x (`authoredup-3m-2026`); practitioner guides say
30 to 90 seconds. **Rule: as long as the proof takes, never padded.** A demo that
takes 40 seconds is a 40 second video.

### 6.5 Voice

- The default is **silent kinetic text** with captions: it works muted, which is
  how the feed plays it.
- A voiceover, when there is one, is **the user's own recorded voice**. A
  synthetic voice speaking in the first person as the user presents something
  the user did not say: it collides with HONESTY.
- **Redundancy principle** (`mayer-multimedia`): with narration, the text on
  screen should be the key phrase, not the full sentence being spoken; the
  captions carry the words for muted viewers.

---

## 7. Images, screenshots and code

### 7.1 Image posts

- Portrait 1080x1350 wins (§2.1). A LinkedIn multi-image post takes up to **20**
  images; keep them all at one aspect ratio, or LinkedIn crops them
  inconsistently (`linkedin-image-specs`).
- **Alt text**, up to **300 characters** on LinkedIn (`linkedin-help-alt-text`):
  what the image shows, including verbatim any text in it that carries meaning,
  such as an error message. LinkedIn may add automatic alt text when none is
  given; write it instead.
- **Quality**: professionally shot, high-quality images raised engagement on both
  Twitter and Instagram; human faces raised it 38% to 291% on Twitter but not on
  Instagram; image-text fit mattered on Twitter (`li-xie-2020`).
  `confidence: high` for quality, platform-dependent for faces.

### 7.2 Screenshots as proof

- **Real captures only.** A frame (browser, window) around a real capture is
  presentation; an invented capture is a lie (`principles.HONESTY`).
- Crop to the part that proves the point. A full web page at feed size proves
  nothing.
- Credit the source on the slide, and put the link in the first comment.
- Redact secrets and personal data before anything is drawn.
- Never capture internal or confidential systems: no client names, no internal
  dashboards, no production prompts (`content/strategy.md`, "what not to post").
- Never capture LinkedIn with a driven browser: the project only uses the
  official API (README).

### 7.3 Code on a slide

- At most about **14 lines and 56 columns**, so it stays at 26px or more.
- Highlight **one to three lines**: the ones the headline talks about.
- No ligatures (`->` must read as two characters), a filename tab, a terminal
  frame for command output.
- Real code and real output, from the user's repository or run. A plausible
  output typed for the slide is a fabricated screenshot.

---

## 8. Color and visual identity

- **Color complexity attracts attention** (`kanuri-2023-ijrm`): images with more
  varied colors drew more attention (eye tracking) and more engagement (two
  Facebook datasets), moderated by time of day, image height and the sentiment
  and complexity of the accompanying text. `confidence: medium`.
- **The tension with legibility**: text needs flat, high-contrast ground.
  **Resolve it by putting the color in the content**, the syntax-highlighted
  code, the diagram, the real screenshot, **not behind the text**.
- **Standing out in the feed**, `confidence: low`: LinkedIn's feed is light by
  default with blue (#0A66C2) interface elements; a dark slide separates from it
  at a glance, and a blue-dominant slide blends into the interface. Practitioner
  guides report dark backgrounds holding contrast better as thumbnails
  (`carousel-color-guides`). Dark mode exists but does not change how a post
  looks to anyone else.
- **Consistency as recognition**, `confidence: low`: every practitioner source
  treats a stable template as what makes a series recognizable; no dataset
  measures it. It is also cheap: signaling and coherence (§4) argue for it on
  their own.
- **Trends are not evidence**: soft gradients, glassmorphism, seamless panoramic
  carousels and "intentionally messy" screenshot carousels are 2026 Instagram
  trends (`instagram-design-trends-2026`). Use only what serves legibility and
  proof.

- **Distinct, not default**: near-black with one acid accent, and cream with a
  terracotta accent, are the two palettes generated designs converge on. A
  palette taken from the subject's own material is harder to mistake for
  anyone else's.

**How the studio applies this**: the identity is a page of engineering work,
taken from the user's positioning ("a measured number instead of an opinion").
`drafting`, the default, is computation paper: pale green with its printed
grid, graphite text, non-photo blue construction lines, and red reserved for
measurements. `blueprint` is the same drawing for dark evidence. The one
memorable device is the dimension line, which measures the reader's place in
the deck and the value on a metric slide. One accent per theme, never per
pillar, and every text and line color tested against WCAG
(`src/linkedin_growth/studio/themes.py`).

---

## 9. The text that goes with each format

- **Carousel caption**: the hook inside the 140 character mobile cutoff; two to
  four short paragraphs of context; what the slides deliver; the closing
  question; "link in the first comment"; zero to three hashtags. The caption
  states the core claim in plain words, because documents take no alt text and
  search reads the caption, not the PDF. Plus a separate **document title**.
- **Image post**: a caption with the weight of a text post (1,000+ characters
  performs, §2.1) and the **alt text**.
- **Video**: a caption, the **SRT file**, and a first frame that states the claim.
- **Text post**: `linkedin-algorithm.md` gives 900 to 1,300 characters as the
  sweet spot; AuthoredUp measures 1,000+ at 1.18x. Both agree that under 300 is
  too short.
- **Cross-posting**, when asked: Instagram takes the same PNG slides with a
  shorter caption; X takes a thread with at most four slide images; Threads takes
  the carousel with a 500 character post, and a text attachment for the long
  version.

---

## 10. Anti-patterns: claims and choices to avoid

| Do not | Why |
|---|---|
| "Video is the best format on LinkedIn" | Only pages and mixed data say so; personal profiles see video below average (§2.1) |
| "85% of LinkedIn videos are watched without sound" | A 2016 Facebook figure from publishers, not a LinkedIn number (§6.3) |
| "The ideal carousel has exactly N slides" | No primary dataset settles it (§3.2) |
| "The ideal video length is N seconds" | The sources disagree by minutes (§6.4) |
| Topic labels as slide headlines | Assertion headlines measurably improve comprehension (§4) |
| A paragraph pasted on a slide | Overlay-heavy posts get fewer likes and comments (§4) |
| Unicode bold or italic in the post | Unreadable by screen readers, invisible to search (§5) |
| A mockup of output that never ran | A fabricated screenshot violates HONESTY (§7.2) |
| Capturing linkedin.com with a browser | The project only uses the official API (§7.2) |
| A synthetic voice narrating as the user | Presents words the user did not say (§6.5) |
| Pages of different sizes in one PDF | LinkedIn rejects or refits them (§3.1) |
| "Salve este post", "comente X" on the closing slide | Engagement bait is forbidden and suppressed (§3.5) |

---

## 11. Source register

| source_id | Organization / authors | Sample | Period | Metric | Nature and declared bias |
|---|---|---|---|---|---|
| `authoredup-3m-2026` | AuthoredUp | 3M+ posts, personal profiles | Mar/2025 to Feb/2026 | Reach and engagement vs each profile's median | Profiles using the tool. [link](https://authoredup.com/blog/best-performing-content-on-linkedin) |
| `buffer-engagement-2026` | Buffer | 52M+ posts, 10 platforms | 2025, with 2024 comparison | Median engagement ÷ reach | Accounts publishing through Buffer. [link](https://buffer.com/resources/state-of-social-media-engagement-2026/) |
| `buffer-threads-vs-x` | Buffer | 10.2M posts on X and Threads | 2024 | Median engagement rate | Same. [link](https://buffer.com/resources/threads-vs-twitter/) |
| `socialinsider-li-2026` | Socialinsider | 1.3M posts, 16,645 business pages | Jan/2024 to Dec/2025 | Engagement ÷ impressions | Business pages only. [link](https://www.socialinsider.io/social-media-benchmarks/linkedin) |
| `socialinsider-ig-2026` | Socialinsider | Business accounts | Q2 2026 | Engagement by followers, reach rate | Business accounts. [link](https://www.socialinsider.io/social-media-benchmarks/instagram) |
| `metricool-li-2026` | Metricool | 673,658 posts, 63,108 accounts | Jan-Feb 2025 vs 2026 | Engagement, impressions | Pages and personal profiles, tool users. [link](https://metricool.com/press-release-linkedin-study-2026/) |
| `metricool-ig-2026` | Metricool | Tool users | 2026 | Saves by format | Press release, method summarized. [link](https://metricool.com/press-release-instagram-study-2026/) |
| `vanderblom-2026` | Richard van der Blom, Algorithm Insights | 1.3M posts, 50,000 creators | 2026 report | Reach, engagement, dwell time | Creators; figures via interview notes. [link](https://podcast.creatorscience.com/richard-van-der-blom-2/) |
| `linkedin-help-documents` | LinkedIn Help | n/a | current | Official limits | Primary. [link](https://www.linkedin.com/help/linkedin/answer/a518909) |
| `linkedin-help-alt-text` | LinkedIn Help | n/a | current | Official limit | Primary. [link](https://www.linkedin.com/help/linkedin/answer/a519856/add-alternative-text-to-images-for-accessibility) |
| `linkedin-video-specs` | LinkedIn specs as compiled by spec guides | n/a | 2026 | Official limits | Secondary compilation. [link](https://www.kapwing.com/resources/linkedin-video-size-guide-aspect-ratios-resolution-length-and-best-practices-3/) |
| `linkedin-image-specs` | Spec guides | n/a | 2026 | Limits | Secondary. [link](https://contentin.io/blog/linkedin-post-specs/) |
| `instagram-grid-2025` | Instagram (Adam Mosseri), via spec guides | n/a | Jan/2025 | Platform change | Primary statement, secondary report. [link](https://www.kapwing.com/resources/instagrams-new-grid-layout-size-and-dimensions-2025/) |
| `meta-safe-zones-2026` | Meta, via ad-spec guides | n/a | Mar/2026 | Safe zone | Secondary. [link](https://www.lucidmedia.co.nz/blog/instagram-facebook-ad-safe-zones-2026/) |
| `x-help-2026` | X Help Center | n/a | current | Official limits | Primary. [link](https://help.x.com/en/using-x/how-to-post) |
| `x-specs-2026` | Spec guides | n/a | 2026 | Crops, sizes | Secondary. [link](https://www.heyorca.com/blog/x-twitter-media-specs-best-practices-2026) |
| `threads-attachments-2025` | Meta Newsroom | n/a | Sep/2025 | Platform feature | Primary. [link](https://about.fb.com/news/2025/09/attach-text-threads-posts-share-longer-perspectives/) |
| `threads-specs-2026` | Spec guides | n/a | 2026 | Limits | Secondary. [link](https://posteverywhere.ai/blog/threads-image-sizes) |
| `mayer-multimedia` | Richard E. Mayer and Logan Fiorella, Cambridge Handbook of Multimedia Learning | Meta-analysis of experiments | 2014 | Learning outcomes, effect sizes | Experimental, education. [link](https://www.cambridge.org/core/books/abs/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/CD5B7AE1279A9AB81F8EEBB53DBEC86E) |
| `garner-alley-2013` | Joanna Garner and Michael Alley, International Journal of Engineering Education | 110 engineering students | 2013 | Comprehension, misconceptions, cognitive load, recall | Experimental. [link](https://writing.engr.psu.edu/ae_comprehension.pdf) |
| `dang-2026-jmr` | Ivy Chu Dang, Canice Kwan, Jayson Jia, Yang Shi, Journal of Marketing Research | Marketer-generated posts | 2026 | Likes and comments | Observational, brand content. [link](https://journals.sagepub.com/doi/10.1177/00222437251373042) |
| `li-xie-2020` | Yiyi Li and Ying Xie, Journal of Marketing Research | Two Twitter datasets, one Instagram | 2020 | Engagement | Observational. [link](https://journals.sagepub.com/doi/10.1177/0022243719881113) |
| `kanuri-2023-ijrm` | Vamsi Kanuri, Christian Hughes, Brady Hodges, International Journal of Research in Marketing | Two Facebook datasets plus two eye-tracking experiments | 2023 | Attention, engagement | Observational plus experimental. [link](https://news.nd.edu/news/high-color-complexity-in-social-media-images-proves-more-eye-catching-increases-user-engagement/) |
| `nngroup-mobile` | Nielsen Norman Group | Reading comprehension study | 2016 | Comprehension, reading speed | Experimental, usability. [link](https://www.nngroup.com/articles/mobile-content/) |
| `wcag-22` | W3C, WCAG 2.2 | n/a | 2023 | Contrast ratios | Standard. [link](https://www.w3.org/TR/WCAG22/#contrast-minimum) |
| `unicode-bold-a11y` | Accessibility writers (m365princess, John Espirian) | n/a | 2025-2026 | Screen reader behaviour | Practitioner, verifiable. [link](https://www.m365princess.com/blogs/bold/) |
| `carousel-typography-guides` | Carouselli, PostNitro | n/a | 2026 | Font sizes | Practitioner. [link](https://postnitro.ai/blog/post/carousel-typography-guide-perfecting-font-sizes-and-spacing) |
| `carousel-color-guides` | Carouselli | n/a | 2026 | Color practice | Practitioner, no data. [link](https://carouselli.com/blog/linkedin-carousel-colors) |
| `instagram-design-trends-2026` | Slidy, Scrolo and others | n/a | 2026 | Trends | Practitioner, no data. [link](https://slidycreator.com/blog/instagram-carousel-trends/) |
| `facebook-iq-2016` | Facebook and Nielsen | Ad campaigns | 2016 | Brand lift over time | Ads, platform research. [link](https://www.marketingdive.com/news/brand-lift-happens-in-less-than-1-second-of-video-study-finds/377333/) |
| `verizon-publicis-2019` | Verizon Media and Publicis Media | Consumer survey | 2019 | Self-reported viewing | Survey. [link](https://www.3playmedia.com/blog/verizon-media-and-publicis-media-find-viewers-want-captions/) |
| `meta-captions` | Meta internal study, via captioning vendors | Ads | 2016 | View time | Secondary. [link](https://www.3playmedia.com/blog/studies-find-captions-improve-engagement/) |
| `digiday-2016` | Digiday | Publisher statements | 2016 | Sound-off views on Facebook | Publisher-reported, not platform data. [link](https://digiday.com/media/silent-world-facebook-video/) |
| `netflix-timed-text` | Netflix Partner Help Center | n/a | current | Caption timing rules | Primary industry standard. [link](https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements) |

---

## 12. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-13 | First compilation: format data for four platforms, carousel and video anatomy, design research, source register. |

### Revalidation triggers

- Buffer, Socialinsider, Metricool or AuthoredUp publish a new edition.
- LinkedIn changes document posts (size, pages, a native carousel returns) or
  announces a video feed change.
- Instagram documents the carousel re-serve behaviour (§2.2) or changes the grid.
- A study with a published method measures carousel slide count or video length
  for personal profiles (§3.2, §6.4).
