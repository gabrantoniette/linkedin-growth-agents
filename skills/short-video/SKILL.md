---
name: short-video
description: Turn a post's narrative into a short feed video (MP4 plus an SRT caption file) built from the studio's slide layouts, timed by reading speed or by the user's own recorded voiceover. Use only when motion is the proof, or when the user asks for video.
---

# Short video

Video is not the default format for a LinkedIn personal profile: personal
profiles see it reach less than their average post (kb-visual-formats.md
§2.1). Use it when the proof moves, or when the asset is also going to Reels or
Threads, where video does well.

## 1. Script it in scenes

- **The first frame states the claim.** 47% of a video's value is delivered in
  the first three seconds (§6.2). No intro, no logo, no "neste vídeo".
- One idea per scene, with the same layouts as a carousel
  (`carousel-design/references/layouts.md`).
- Five to ten scenes. As long as the proof takes, never padded: 30 to 75
  seconds covers most posts.
- **Built for sound off.** The text on screen carries the story; most feed
  video is watched muted (§6.3).

## 2. Narration and captions

- `narration` on a scene is what is said while it is on screen. It becomes
  burned-in captions and `captions.srt`.
- Captions follow the rules in §6.3: at most two lines of 42 characters, at 17
  characters per second. The render warns when a scene is too short for its
  narration; lengthen the scene or cut the narration.
- With narration, the slide keeps only the key phrase and the captions carry
  the full sentence (the redundancy principle, §6.5).
- **Voice**: only a recording of the user, saved under content/ and pointed at
  by `voiceover`. Never synthetic speech in the user's name. Without a
  recording, the video is silent, with the narration as captions or with no
  narration at all.

## 3. The spec

```yaml
title: "O título, também usado no nome do arquivo"
aspect: "4:5"          # "9:16" for Reels and vertical feeds; "1:1" rarely
theme: drafting
burn_captions: true
voiceover: media/<slug>/voiceover.m4a   # optional, the user's own recording
scenes:
  - layout: cover
    headline: "..."
    narration: "..."   # optional
    duration: 3.5       # optional; computed from reading time when omitted
```

## 4. Render and review

Call `render_video(slug, spec)`. Read the timing warnings, look at the contact
sheet of scenes, and check `cover.png`: it is the frame LinkedIn shows before
anyone presses play, so it has to carry the hook on its own.

## 5. What the user does by hand

Upload `video.mp4` in the LinkedIn composer, add `captions.srt` through the
caption option, and pick `cover.png` as the thumbnail if the composer offers it.
The system never publishes video.
