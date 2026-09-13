"""Video timing and captions: pure arithmetic, no browser and no ffmpeg.

The caption rules come from the Netflix Timed Text Style Guide
(kb-visual-formats.md §6.3): two lines of 42 characters at most, read at 17
characters per second. A caption that breaks them is text nobody finishes.
"""

from __future__ import annotations

import pytest

from linkedin_growth.studio.spec import parse_spec
from linkedin_growth.studio.video import (
    CAPTION_LINE,
    CAPTION_LINES,
    MAX_SCENE_SECONDS,
    MIN_SCENE_SECONDS,
    plan,
    split_caption,
    srt_time,
    to_srt,
)

NARRATION = (
    "Antes de mexer em qualquer coisa no meu RAG, eu medi onde o tempo de cada "
    "resposta estava indo."
)


def video(*scenes: dict, **deck):
    spec, problems = parse_spec({"title": "T", **deck, "scenes": list(scenes)}, "video")
    assert spec is not None, problems
    return spec


def test_every_caption_event_fits_two_lines_of_42_characters():
    for event in split_caption(" ".join([NARRATION] * 4)):
        lines = event.split("\n")
        assert len(lines) <= CAPTION_LINES
        assert all(len(line) <= CAPTION_LINE for line in lines)


def test_events_are_balanced_and_cut_where_a_speaker_breathes():
    """Regression: the greedy split left 'estava indo.' alone, on screen for under a second."""
    events = [event.replace("\n", " ") for event in split_caption(NARRATION)]

    assert events == [
        "Antes de mexer em qualquer coisa no meu RAG,",
        "eu medi onde o tempo de cada resposta estava indo.",
    ]


def test_the_two_lines_of_an_event_are_balanced():
    first = split_caption(NARRATION)[0].split("\n")

    assert first == ["Antes de mexer em qualquer", "coisa no meu RAG,"]


def test_a_short_narration_is_one_event_on_one_line():
    assert split_caption("Curta e direta.") == ["Curta e direta."]


def test_scene_duration_follows_reading_time_within_bounds():
    short = video({"layout": "statement", "text": "Oi"})
    long = video({"layout": "statement", "text": "palavra " * 30})

    assert plan(short)[0].scenes[0].duration == pytest.approx(MIN_SCENE_SECONDS)
    assert plan(long)[0].scenes[0].duration == pytest.approx(MAX_SCENE_SECONDS)


def test_an_explicit_duration_wins():
    spec = video({"layout": "statement", "text": "Oi", "duration": 4.25})

    assert plan(spec)[0].total == pytest.approx(4.25)


def test_a_voiceover_sets_the_length_and_keeps_the_proportions():
    """The voice sets the pace; the picture follows it."""
    spec = video({"layout": "statement", "text": "Oi"}, {"layout": "statement", "text": "palavra " * 20})

    natural, _ = plan(spec)
    voiced, _ = plan(spec, audio_seconds=30.0)

    assert voiced.total == pytest.approx(30.0)
    assert voiced.scenes[0].duration / voiced.scenes[1].duration == pytest.approx(
        natural.scenes[0].duration / natural.scenes[1].duration
    )


def test_cues_stay_inside_their_scene_and_in_order():
    spec = video(
        {"layout": "cover", "headline": "Capa", "narration": NARRATION},
        {"layout": "closing", "headline": "Fim", "narration": "E você, mediu?"},
    )

    timeline, _ = plan(spec)

    for scene in timeline.scenes:
        for cue in scene.cues:
            assert scene.start <= cue.start < cue.end <= scene.end + 1e-9
    starts = [cue.start for cue in timeline.cues]
    assert starts == sorted(starts)


def test_srt_timestamps_use_the_subrip_format():
    assert srt_time(0) == "00:00:00,000"
    assert srt_time(3725.5) == "01:02:05,500"


def test_srt_numbers_cues_from_one():
    srt = to_srt(plan(video({"layout": "cover", "headline": "Capa", "narration": NARRATION}))[0])

    assert srt.startswith("1\n00:00:00,000 --> ")
    assert "\n2\n" in srt
