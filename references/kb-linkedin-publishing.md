---
id: kb-linkedin-publishing
title: "Reference base — Timing, frequency and format of LinkedIn publishing"
version: 1.0
compiled_on: 2026-09-12
revalidate_on: 2026-12-12
language: en
scope:
  - day_of_week
  - time_of_day
  - weekly_frequency
  - content_format
  - algorithm_mechanics
  - brazilian_market
out_of_scope:
  - linkedin_ads
  - recruiting_and_sourcing
  - copywriting_and_hooks
  - social_selling_and_outbound
global_confidence: medium
evidence_nature: observational
has_controlled_experiment: false
---

# Reference base — Publishing on LinkedIn

A compilation of six primary studies published between late 2025 and September 2026,
covering more than 10 million posts. The document exists to serve as factual context for
agents that recommend a publishing strategy.

---

## 0. Instructions for the agent

Rules of conduct when using this document as a source:

1. **Never present a time of day as settled fact.** The studies diverge by ~7 hours.
   Every time-of-day recommendation must carry the divergence with it (§3.2).
2. **Always distinguish a personal profile from a company page.** The two populations
   behave differently, and most studies mix them without saying so.
3. **Always distinguish a per-post metric from a per-week metric.** It is the most common
   analytical error in this domain (§4.1).
4. **The user's own data beats this document.** If the user brings their own analytics,
   that is the final authority; this base becomes the opening hypothesis.
5. **Times are always in the target audience's local timezone**, not the publisher's. For
   a Brazilian audience, read everything as Brasília time.
6. **No study here has a cut for Brazil.** See §7 before applying any of it to a Brazilian
   audience.
7. When citing a number, cite the matching `source_id` too (§10).
8. If the user's question falls under `out_of_scope`, state the gap instead of inferring.

---

## 1. Canonical parameters

A parseable block with the consensus values. The `confidence` fields: `high` = every study
agrees; `medium` = most agree; `low` = open divergence.

```json
{
  "days": {
    "strong_block": ["tuesday", "wednesday", "thursday"],
    "acceptable_block": ["monday"],
    "weak_block": ["friday"],
    "avoid_block": ["saturday", "sunday"],
    "best_single_day": {"value": "wednesday_or_tuesday", "confidence": "medium"},
    "confidence": "high"
  },
  "times": {
    "overlap_window_across_studies": "10:00-16:00",
    "alternative_morning_window": "07:00-09:00",
    "alternative_afternoon_window": "15:00-20:00",
    "most_cited_slot": {"value": "wednesday_16h", "confidence": "medium"},
    "hour_of_highest_posting_volume": "09:00",
    "confidence": "low",
    "divergence_amplitude_hours": 7
  },
  "personal_profile_frequency": {
    "sustainable_weekly_floor": 2,
    "recommended_weekly_range": [3, 5],
    "acceleration_weekly_range": [6, 10],
    "ceiling_with_detected_penalty": null,
    "minimum_spacing_between_posts_hours": 24,
    "confidence": "high"
  },
  "formats_by_engagement_desc": [
    "pdf_carousel",
    "video",
    "image",
    "text",
    "post_with_link_in_body"
  ],
  "link_rule": "link in the first comment, never in the post body",
  "impact_hierarchy_desc": ["consistency", "format", "frequency", "time_of_day"]
}
```

---

## 2. Days of the week

### 2.1 Consensus

The single point where every dataset converges: **the Tuesday–Thursday block dominates and
the weekend collapses**. LinkedIn is coupled to the working week in a way no other social
platform is. `confidence: high`

| Study | Declared best day |
|---|---|
| Buffer 2026 | Wednesday, then Thursday and Friday |
| Sprout Social 2026 | Tuesday, Wednesday, Thursday |
| MagicPost 2026 | Tuesday |
| Hootsuite + Critical Truth | Tuesday and Wednesday |
| SocialPilot 2026 | Tuesday, Wednesday, Thursday |
| Metricool 2026 | Monday, Tuesday, Wednesday |

### 2.2 Quantifying the gradient

MagicPost measured real impressions across 831,350 posts from 10,798 creators and counted
which day each creator got their widest reach. Index with Tuesday = 100:

| Day | Reach index | Creators |
|---|---|---|
| Monday | 95 | 1,980 |
| **Tuesday** | **100** | **2,075** |
| Wednesday | 91 | 1,886 |
| Thursday | 92 | 1,900 |
| Friday | 77 | 1,607 |
| Saturday | 33 | 685 |
| Sunday | 32 | 665 |

**The correct reading:** Monday through Thursday form a statistically tight plateau
(91–100). The gap between "the best day" and "the fourth best day" is small. The real cut
is between the working week and the weekend, not between Tuesday and Wednesday.

**Divergence to preserve:** Buffer ranks Monday and Tuesday as the *worst* weekdays, while
MagicPost puts Monday second and Hootsuite puts Tuesday first. Do not assert an internal
ranking of the working week with confidence.

---

## 3. Times of day

### 3.1 Structural caveat

No study measures **real visits**. LinkedIn and Microsoft do not release sessions by
day or hour. Every number below is a proxy, of three distinct kinds:

- **Engagement per day×hour slot** — a proxy for an active audience. The most used one.
- **Posting volume** — measures supply (feed congestion), not demand.
- **Aggregate web traffic** — monthly, with no hourly cut.

### 3.2 The divergence (do not flatten it)

| Study | Sample | Metric | Verdict |
|---|---|---|---|
| Hootsuite | 1M+ posts, 118 countries | Raw engagement | 08:00–09:00, Tue/Wed |
| MagicPost | 2,667,049 posts | Normalized per author | 07:00–09:00, weekdays |
| Metricool | 673,658 posts / 63,108 accounts | Engagement | 09:00–12:00 |
| SocialPilot | 683,000 posts / 47,672 accounts | Engagement | 10:00–12:00 and 13:00–16:00 |
| Sprout Social | ~2B interactions / 307k profiles | Raw engagement | 11:00–17:00 |
| Buffer | 4.8M posts | Raw engagement | 15:00–20:00, peak Wed 16:00 |

**Amplitude: ~7 hours between the earliest and the latest extreme.**

### 3.3 Why they diverge — identified causes

| Cause | Effect |
|---|---|
| **Metric** | Raw engagement rewards the hours when large accounts publish. Company pages run on an office schedule → pulls the result into the afternoon. MagicPost normalized against each author's own historical average → the result migrates to the morning. |
| **Population** | Individual creators vs. company pages. Pages show ~1.7x more variation between their best and worst day than personal profiles do (AuthoredUp, 3M+ posts). Mixing the two buries the hour signal. |
| **Timezone** | Buffer, Sprout and MagicPost normalize to the audience's local time. The others do not say. Comparing tables without checking this produces systematic error. |
| **Collection window** | Sprout collected from 2025-11-27 to 2026-02-27 — which includes northern-hemisphere holidays, where most of the sample is. |
| **Portfolio bias** | Each tool analyzes its own customers. Different customer profiles produce different hours. |

**Derived rule:** if the user has a personal profile and publishes as an individual,
prioritize the MagicPost finding (early morning). If they run a company page, prioritize
Buffer/Sprout (midday to afternoon).

### 3.4 Grid by day — Buffer (mixed profiles, raw engagement)

| Day | 1st | 2nd | 3rd |
|---|---|---|---|
| Monday | 22:00 | 17:00 | 21:00 |
| Tuesday | 16:00 | 17:00 | 22:00 |
| Wednesday | **16:00** | 15:00 | 17:00 |
| Thursday | 17:00 | 19:00 | 21:00 |
| Friday | 15:00 | 16:00 | 17:00 |
| Saturday | 09:00 | 18:00 | 22:00 |
| Sunday | 22:00 | 21:00 | 06:00 |

### 3.5 Grid by day — Sprout Social (raw engagement, ~2B interactions)

| Day | Peak window |
|---|---|
| Monday | 13:00–14:00 |
| Tuesday | 11:00–17:00 |
| Wednesday | 11:00–16:00 |
| Thursday | 11:00 and 13:00–17:00 |
| Friday | 11:00 and 13:00–14:00 |
| Saturday / Sunday | no optimal window |

### 3.6 Cross-cutting finding: the crowd's hour ≠ the performing hour

MagicPost separated **when most people publish** from **when posts do best**. They are not
the same hour, and the pattern repeats across every large market measured.

| Market | Crowd hour | Score | Best hour | Score |
|---|---|---|---|---|
| US (Eastern) | 09:00 | 72 | 08:00 | 80 |
| United Kingdom | 09:00 | 73 | 07:00 | 86 |
| France (Paris) | 08:00 | 57 | 07:00 | 70 |
| India (IST) | 10:00 | 68 | 08:00 | 81 |
| Global (UTC) | 07:00 | 61 | 06:00 | 66 |

Magnitudes, as examples: in the US, 09:00 concentrates 69,398 weekday posts; at 08:00 the
volume is ~25% lower and the score goes up. In France, 08:00 is the single biggest hour of
any country measured (138,029 posts) and scores 57; 07:00, with a fifth of the volume,
scores 70.

**Derived rule:** publish 1 to 2 hours before the local posting peak. If the question is
"where is the most traffic", the literal answer is 09:00 local — but posting volume is
congestion, not opportunity.

---

## 4. Weekly frequency (individual profile)

### 4.1 The central analytical error

A **per-post** metric and a **per-week** metric move in opposite directions as frequency
rises. Anyone watching engagement/post concludes that raising cadence is hurting
performance and pulls back — an inverted conclusion.

MagicPost, the 1,000–10,000 follower band (~15,000 creators in the sample):

| Pace | Median likes/post | Median likes/week |
|---|---|---|
| < 2 per month | 29 | 11 |
| 2–4 per month | 21 | 21 |
| 1–2 per week | 18 | 35 |
| 2–4 per week | 15 | 58 |
| ~daily | 13 | 87 |
| > daily | 8 | 114 |

Whoever publishes 2–4 times a week accumulates ~5x the weekly engagement of whoever
publishes less than twice a month. At a daily pace, ~8x.

**The correct denominator: the week.**

### 4.2 By follower band (median likes/week)

| Pace | < 1k | 1k–10k | 10k–50k | 50k+ |
|---|---|---|---|---|
| < 2 per month | 4 | 11 | 23 | 161 |
| 1–2 per week | 12 | 35 | 91 | 521 |
| ~daily | 25 | 87 | 235 | 1,156 |

The "more frequency, more weekly total" pattern holds in every band.

### 4.3 Marginal gain — Buffer (the best methodological design)

Buffer compared **the same account** across high- and low-frequency weeks, using a Z-score
against its own average plus fixed-effects regression, over 2M+ posts from 94k+ accounts.

| Frequency | Gain vs. 1 post/week |
|---|---|
| 2–5 per week | +1,182 impressions/post, +0.23 pp of engagement rate |
| 6–10 per week | +5,001 impressions/post, +0.76 pp |
| 11+ per week | +16,946 impressions/post, ~3x engagements, +1.40 pp |

Two findings:
- The effect is **independent of account size**. Accounts with a few hundred followers saw
  the same relative gain going from 1 to 2–5 posts as accounts with tens of thousands.
- **Diminishing marginal returns.** The jump from 1 → 2–5 is bigger than the jump from
  6–10 → 11+.

### 4.4 Benchmark of real behavior

- The most common pace in the 1k–10k follower band: **1–2 posts per week** (~25% of creators).
- Daily publishers are a minority in that band; above 1x/day is under 2%.
- Metricool average: personal profiles 3.05 posts/week; company pages 2.34.
- LinkedIn's official recommendation: 1 to 5 per week — 1 to 3 short posts weekly and
  1 to 2 long articles per month.
- Only ~3% of LinkedIn members publish more than once a week. Publishing with any
  regularity at all already puts a profile in a narrow minority.

### 4.5 The cannibalization thesis — status: unsupported

It circulates widely that publishing too much makes your posts compete with each other and
the algorithm suppress reach. Guides exist claiming that above 1 post/day the reach per
post falls because the algorithm avoids showing two posts from the same author to the same
user within a short window.

**Neither of the two studies with primary data found that cliff.** Neither Buffer nor
MagicPost identified any frequency level at which the weekly total started to fall,
including above two posts per day.

Treat cannibalization as a claim with no public dataset behind it. Do not repeat it as fact.

---

## 5. Content format

Moves the result more than climbing one slot in weekly cadence does. Median engagement,
Buffer data:

| Format | Relative performance |
|---|---|
| **Carousel (native PDF)** | ~278% above video, ~303% above image, ~600% above text |
| Video | ~84% above text |
| Image | ~72% above text |
| Plain text | The engagement floor, but the format that sustains the habit |
| Post with a link in the body | The worst rate of all — it takes the user off the platform |

**Derived rules:**
- Link always in the first comment, never in the body.
- Technical and instructional content (architecture, comparing approaches, step by step,
  troubleshooting) is naturally sequential and converts better as a carousel than as a
  block of text.
- Start with the formats that sustain consistency (text, image) and add carousel and video
  once the rhythm exists.

---

## 6. Algorithm mechanics (state in 2026)

### 6.1 What changed

LinkedIn moved to distributing content by **relevance** rather than recency alone. The
operational consequence: a post can re-enter distribution days after publication, which
reduces the weight of the exact hour.

### 6.2 Golden hour — status: a concept, not a confirmed rule

The 60–90 minute window after publishing is widely cited, but **LinkedIn has never
officially confirmed a 60- or 90-minute window**. Treat it as a heuristic, not as a
documented mechanism.

### 6.3 The signal that actually scales

AuthoredUp's analysis of 3M+ posts: publications that earn **saves and substantive
comments between 24 and 72 hours** after publishing perform **4 to 6 times better** in
suggested feeds than publications that only got fast, shallow engagement at the start.

That favors content with a long half-life and lowers the pressure on volume and on timing.

### 6.4 Comments as a parallel channel

LinkedIn started counting impressions for comments, which effectively turns a comment into
a micro-post with reach outside the author's network.

**Derived rule:** in low-capacity weeks, 2–3 posts plus 10–15 daily minutes of comments
that carry a point of view deliver visibility comparable to a higher cadence. A generic
comment ("great content!") does not count.

---

## 7. The Brazilian context

### 7.1 Size of the market

| Metric | Value | Date |
|---|---|---|
| Users in Brazil | 100 million | Jun 2026 |
| Global position | 3rd largest market (behind the US and India) | Jun 2026 |
| Penetration of the economically active population (~108M) | ~90% | Jun 2026 |
| New profiles per day | 8,000 to 12,000 | Jun 2026 |
| Original content published in the quarter | 11+ million | quarter before Jun 2026 |
| Interactions generated in the quarter | ~400 million | quarter before Jun 2026 |

### 7.2 The critical gap

**None of the six studies publishes a cut for Brazil.** MagicPost, the only one with a
per-country cut in local time, covers nine markets (US, United Kingdom, France, Germany,
India, Netherlands, Pakistan, Australia, Canada) and Brazil is not among them.

Every hour grid in this document is a global average dominated by the US, India, the
United Kingdom and France. Applying them to Brazil is extrapolation, not measurement.

The agent **must declare this gap** when recommending times for a Brazilian audience.

### 7.3 Starting grid for a Brazilian audience (Brasília time)

Built from the convergence between studies. **Status: a hypothesis to test, not a finding.**

| | Mon | Tue | Wed | Thu | Fri |
|---|---|---|---|---|---|
| Morning slot | — | 08:00 | 08:00 | 08:00 | — |
| Midday slot | 13:00 | 11:00–12:00 | 11:00–12:00 | 11:00–12:00 | 11:00 |
| Afternoon slot | — | 16:00 | **16:00** | 16:00 | 15:00 |

Wednesday at 16:00 is the only slot that shows up strongly across multiple independent
studies.

---

## 8. Protocol for measuring your own

Given that the studies diverge by 7 hours and none covers Brazil, measuring is the only
way out.

### 8.1 Collection

- Export the CSV from LinkedIn Analytics (Page → Analytics → Content → Export).
- **Known limitation:** the native analytics does not preserve the exact publication
  timestamp after the fact — it shows only relative time ("3h", "2d"). You have to record
  the publishing hour in parallel, or publish through a tool that records it.

### 8.2 Modeling

Grain: `post_id × day_of_week × hour × format`

Metrics: impressions, engagement, clicks, saves, comments.

### 8.3 Mandatory normalization

Normalize each post against the **profile's own 90-day moving average**. Without that,
follower growth contaminates the time series and produces the false conclusion that "the
hours got better" when only the audience grew.

### 8.4 Minimum volume

Do not conclude anything with fewer than **10 to 15 posts per slot tested**. Below that, a
single viral post moves the whole average.

### 8.5 Test window

Hold the grid fixed for **2 to 4 weeks** before adjusting. Changing the hour every week
makes it impossible to accumulate statistical volume.

---

## 9. Anti-patterns — claims the agent must not make

| Do not claim | Reason |
|---|---|
| "The best time to post is X" (unqualified) | ~7h divergence between studies with primary data |
| "Posting too much cannibalizes your reach" | Unsupported by the two datasets that measured it |
| "The algorithm judges your post in the first 60 minutes" | LinkedIn never confirmed the window; distribution became continuous |
| "These are the best times in Brazil" | No study has a cut for Brazil |
| "Wednesday is the best day" (as fact) | Buffer says Wednesday, MagicPost and Hootsuite say Tuesday |
| "Your engagement per post fell, reduce your frequency" | Wrong denominator; measure per week |
| "Post every day to grow" | True in aggregate, but an abandoned cadence is worse than a smaller one that is kept |

### 9.1 Methodological limitation to declare when relevant

No study here is a controlled experiment.

- **MagicPost** is correlational and declares its own bias: the sample comes from profiles
  the tool tracks, skewed toward people who take LinkedIn seriously. Part of the gain
  attributed to frequency may be investment in quality, not frequency.
- **Buffer** solves the selection bias *between* accounts with fixed effects, but not the
  week-level confounder: a week with 6 publications was probably also a week with more
  time, more energy and better material. The direction of the recommendation is safe; the
  magnitude is not.

---

## 10. Source register

| source_id | Organization | Sample | Period | Metric | Declared bias |
|---|---|---|---|---|---|
| `buffer-timing-2026` | Buffer | 4.8M posts | pub. Sep 2026 | Raw engagement | Accounts that publish through Buffer |
| `buffer-freq-2026` | Buffer | 2M+ posts / 94k+ accounts | 2025–2026 | Impressions, engagement, rate (Z-score + fixed effects) | Same |
| `sprout-2026` | Sprout Social | ~2B interactions / 307k profiles | Nov 2025–Feb 2026 | Raw engagement | Sprout's portfolio; 6 networks |
| `magicpost-timing-2026` | MagicPost | 2,667,049 posts | through May 2026 | Score normalized per author, per country | Individual creators who use the tool |
| `magicpost-day-2026` | MagicPost | 831,350 posts / 10,798 creators | May 2026 | Real impressions | Same |
| `magicpost-freq-2026` | MagicPost | 26,428 creators | 12 months through Jun 2026 | Median likes per post and per week | Same |
| `metricool-2026` | Metricool | 673,658 posts / 63,108 accounts | 2026 | Engagement | Metricool's portfolio |
| `hootsuite-critical-truth` | Hootsuite + Critical Truth | 1M+ posts / 118 countries | 2025 | Engagement | Hootsuite's portfolio |
| `socialpilot-2026` | SocialPilot | 683,000 posts / 47,672 accounts | 2026 | Engagement | SocialPilot's portfolio |
| `authoredup-3m` | AuthoredUp | 3M+ posts | 2026 | Distribution in suggested feeds | Not declared |
| `linkedin-br-2026` | LinkedIn (official announcement) | — | Jun 2026 | User count | The platform's own primary source |

### 10.1 Global platform context

| Metric | Value | Source |
|---|---|---|
| Registered members | ~1.3 billion | LinkedIn / DataReportal |
| Monthly active users | ~310 million (~28% of registered) | Microsoft, Q2 FY2026 results |
| Monthly visits to the site | ~1.9–2.0 billion | Similarweb, Mar–May 2026 |
| Daily access rate | 16.2% | DataReportal |
| Monthly access rate | 48.5% | DataReportal |
| Users who interact with brand content at least 1x/week | ~70% | Sprout Social, 2026 Content Strategy Report |
| Members who publish more than 1x/week | ~3% | LinkedIn DSA / aggregate analyses |

---

## 11. Decision hierarchy

The order of impact on the result, from largest to smallest. An agent that needs to
prioritize recommendations should follow this order:

1. **Consistency** — a cadence kept for 90+ days
2. **Format** — carousel > video > image > text; link outside the body
3. **Frequency** — 3 to 5 per week as the target, 2 as the floor
4. **Time of day** — a tiebreaker, not a lever

Rationale: the difference between the best hour slot and the ordinary plateau is real and
measurable, but smaller than the difference between formats and much smaller than the
difference between publishing and not publishing. The biggest jump in the whole dataset is
between silence and any rhythm at all.

---

## 12. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-09-12 | Initial compilation. Six primary studies + the Brazilian context. |

### Revalidation triggers

Review this document when any of the events below happens:

- Buffer, Sprout, Metricool, Hootsuite, SocialPilot or MagicPost publish an annual refresh
- LinkedIn announces a change to the distribution algorithm
- Any study publishes a cut specific to Brazil (that would close the gap in §7.2)
- A controlled experiment on frequency appears (that would change the status of §4.5 and §9.1)
