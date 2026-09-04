# LinkedIn algorithm heuristics (2026)

Adapted from [sergebulaev/linkedin-skills](https://github.com/sergebulaev/linkedin-skills)
(MIT), the `linkedin-post-writer` skill / `references/algorithm-heuristics.md`.
These are figures from external research (the 360Brew paper, arXiv 2501.16450;
AuthoredUp 2026 benchmarks; reporting on pod moderation). Treat them as
directional, not as guarantees, and distrust any number that looks too good.

This is a reference on **format and mechanics**, not on content. The rules on
honesty, positioning and voice stay in `principles.py` and outrank any algorithm
heuristic here.

## Length

- Sweet spot: 900-1,300 characters (about 150-220 words), which lines up with
  the existing 120-250 word rule.
- Hook cutoff: **about 140 characters on mobile** before "see more" (about 210
  on desktop). Write the hook for the mobile cutoff.
- A long post (1,500-1,900) only works with a line break every one or two
  sentences and a real narrative payoff at the end.

## Hashtags

- **Zero to three highly specific hashtags** perform the same or better than
  five or more in 2026: the ranker uses semantic embeddings and no longer does
  tag matching.
- **Five or more hashtags correlates with spam-account behaviour** (a negative
  signal). This supersedes any older "three to five hashtags" rule.
- Hashtags go at the end of the post, never mid-sentence.

## External links

- A link in the post body: **roughly a 40-60% drop in reach**.
- A link in the first comment: about twice the impressions of a link in the body.
- If the post cites an external source, write "fonte no primeiro comentário" and
  leave the link there, not in the post.

## The first 60-90 minutes (the "momentum window")

- That window decides roughly 80% of a post's total reach.
- Replying to every comment within the first 90 minutes is what determines
  whether the post reaches its ceiling.
- Three or more substantive comments in the first 30 minutes give a second
  distribution push.

## Quality signals (not officially confirmed, but reported)

- A "save" weighs about 5x a like and about 2x a comment.
- A paragraph-length comment weighs about 4x a one-word reaction.
- A comment the author replies to counts as a fresh signal on each reply.
- Ideal read time: 31-60 seconds.
- "See more" followed by a fast bounce (under 3s) is penalized as clickbait.

## What gets penalized

- Asking for engagement generically ("concorda? comenta aí") is actively
  suppressed. It was already forbidden by `DO_NOT`, and now it carries a
  technical penalty as well as a reputational one.
- Engagement-pod patterns (the same accounts commenting in the same minute every
  day) are detected and cut reach for weeks. Not a real risk for an organic
  personal account, but it explains why it never pays to ask friends to "help
  out" by commenting at the same time.
- A generic closing question ("o que vocês acham?") gets 20-40% less engagement
  than a specific question naming the topic. Already a project rule; the data
  only confirms it.

## Checklist before publishing

- [ ] The hook fits in the ~140 character mobile cutoff
- [ ] No em dash (—) and no en dash (–). See `ai-vocabulary.md`
- [ ] At least one specific number per ~100 words
- [ ] At least one proper noun, tool or concrete project
- [ ] At least one first-person detail (what you saw, did, decided)
- [ ] No link in the post body. The link goes in the first comment
- [ ] Zero to three hashtags, specific, only at the end
- [ ] Line breaks between ideas, not after every sentence
- [ ] The closing is a specific question, or a clean ending. Never
      "o que vocês acham?"
