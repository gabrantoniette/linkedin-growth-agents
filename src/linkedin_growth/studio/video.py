"""Video: the deck's own slides, animated, encoded to MP4, with captions.

A feed video built from the same layouts as the carousel, so a post and its
video look like the same author made them. Each scene enters with a short
animation, then holds for as long as its text takes to read, and the narration,
when there is one, becomes both burned-in captions and an `.srt` file.

What it deliberately does not do:

- **No synthetic voice.** The voiceover, if any, is a recording of the user.
  A generated voice speaking in the first person as the user would put words in
  their mouth, and HONESTY forbids that (kb-visual-formats.md §6.5).
- **No stock footage, no music.** Nothing in the frame that the user did not
  make or cannot license.

How a frame gets made: the page is loaded once with every scene, all CSS
animations are paused, and for each frame the animations are seeked to an exact
time before a screenshot. That makes the video deterministic, frame for frame,
which a screen recording never is. Holds are one screenshot shown for a
duration, so a 40 second video is a few hundred images, not 1,200.

The timing constants come from the caption rules in kb-visual-formats.md §6.3.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

from linkedin_growth.config import CONTENT_DIR
from linkedin_growth.studio.brand import resolve_asset_path
from linkedin_growth.studio.browser import Studio, run_isolated
from linkedin_growth.studio.carousel import fit_problems, make_contact_sheet
from linkedin_growth.studio.html import FIT_SCRIPT, build_document
from linkedin_growth.studio.lint import VIDEO_WARN_SECONDS, lint, reading_text
from linkedin_growth.studio.safety import confine
from linkedin_growth.studio.spec import Author, CodeSlide, VideoSpec, dump_spec, text_errors
from linkedin_growth.studio.text import plain
from linkedin_growth.studio.themes import VIDEO_SIZES

# Timing

# The longest entrance in studio.css (0.75s plus the last stagger) with a margin.
ENTRANCE_SECONDS = 0.9

# Netflix's adult reading-speed ceiling for Portuguese and most Latin-script
# languages. A caption or slide faster than this is text nobody finishes.
READING_CPS = 17.0

# A pause after the text is read, before the cut. Without it the video feels
# like it is being scrolled past the viewer.
BREATH_SECONDS = 0.7

MIN_SCENE_SECONDS = 2.5
MAX_SCENE_SECONDS = 9.0

# Code is read slower than prose: symbols, and the eye goes back to check.
CODE_EXTRA_SECONDS = 2.0

# Caption events: at most two lines of 42 characters, on screen between 5/6 of
# a second and 7 seconds (Netflix Timed Text Style Guide).
CAPTION_LINE = 42
CAPTION_LINES = 2
CAPTION_MIN_SECONDS = 5 / 6
CAPTION_MAX_SECONDS = 7.0

FADE_OUT_SECONDS = 0.35

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}

# Seeks every animation of one scene to an exact time and sets its caption.
SEEK_SCRIPT = """({ index, ms, caption }) => {
  const slide = document.querySelectorAll('.slide')[index];
  for (const animation of slide.getAnimations({ subtree: true })) {
    animation.pause();
    animation.currentTime = ms;
  }
  const band = slide.querySelector('.burned-caption span');
  if (band) band.textContent = caption || '';
}"""


@dataclass
class Cue:
    start: float
    end: float
    # Already wrapped: at most two lines, joined by a newline.
    text: str


@dataclass
class ScenePlan:
    index: int
    start: float
    duration: float
    cues: list[Cue] = field(default_factory=list)

    @property
    def end(self) -> float:
        return self.start + self.duration

    def caption_at(self, moment: float) -> str:
        for cue in self.cues:
            if cue.start <= moment < cue.end:
                return cue.text
        return ""


@dataclass
class Timeline:
    scenes: list[ScenePlan]

    @property
    def total(self) -> float:
        return self.scenes[-1].end if self.scenes else 0.0

    @property
    def cues(self) -> list[Cue]:
        return [cue for scene in self.scenes for cue in scene.cues]


def reading_seconds(text: str | None) -> float:
    return len(plain(text or "")) / READING_CPS


def natural_duration(scene: object) -> float:
    """How long a scene stays on screen when the spec does not say."""
    explicit = getattr(scene, "duration", None)
    if explicit:
        return float(explicit)
    on_screen = reading_seconds(reading_text(scene))
    if isinstance(scene, CodeSlide):
        on_screen += CODE_EXTRA_SECONDS
    spoken = reading_seconds(getattr(scene, "narration", None))
    seconds = ENTRANCE_SECONDS + max(on_screen, spoken) + BREATH_SECONDS
    return min(MAX_SCENE_SECONDS, max(MIN_SCENE_SECONDS, seconds))


def _wrap(text: str) -> list[str]:
    """One caption event as lines: one when it fits, two of similar length when not.

    Balanced rather than greedy, so an event of 44 characters becomes 26 and 17,
    not 42 and a lonely word on the second line.
    """
    if len(text) <= CAPTION_LINE:
        return [text]
    middle = len(text) / 2
    cuts = [
        index
        for index, char in enumerate(text)
        if char == " " and index <= CAPTION_LINE and len(text) - index - 1 <= CAPTION_LINE
    ]
    if cuts:
        cut = min(cuts, key=lambda index: abs(index - middle))
        return [text[:cut], text[cut + 1 :]]
    return textwrap.wrap(text, width=CAPTION_LINE, break_long_words=True, break_on_hyphens=False)


def _pause_bonus(word: str, target: float) -> float:
    """How much a cut after `word` is worth: a period more than a comma."""
    if re.search(r"[.!?…]$", word):
        return (target * 0.6) ** 2
    if re.search(r"[,;:]$", word):
        return (target * 0.35) ** 2
    return 0.0


def _split(words: list[str], count: int) -> list[str] | None:
    """The best split of `words` into `count` events that each fit two lines.

    Dynamic programming over the cut positions. The cost of a split is how far
    each event is from the average length, minus a bonus for every cut that
    lands on punctuation, so a caption ends where a speaker would breathe.
    """
    total = len(words)
    target = len(" ".join(words)) / count
    infinity = float("inf")
    cost = [[infinity] * (total + 1) for _ in range(count + 1)]
    start = [[0] * (total + 1) for _ in range(count + 1)]
    cost[0][0] = 0.0
    for events in range(1, count + 1):
        for end in range(1, total + 1):
            for begin in range(end - 1, -1, -1):
                event = " ".join(words[begin:end])
                if len(event) > CAPTION_LINE * CAPTION_LINES:
                    break
                if cost[events - 1][begin] == infinity or len(_wrap(event)) > CAPTION_LINES:
                    continue
                value = cost[events - 1][begin] + (len(event) - target) ** 2
                if end < total:
                    value -= _pause_bonus(words[end - 1], target)
                if value < cost[events][end]:
                    cost[events][end] = value
                    start[events][end] = begin
    if cost[count][total] == infinity:
        return None
    pieces: list[str] = []
    end = total
    for events in range(count, 0, -1):
        begin = start[events][end]
        pieces.append(" ".join(words[begin:end]))
        end = begin
    return pieces[::-1]


def split_caption(narration: str) -> list[str]:
    """Narration -> caption events of at most two 42-character lines.

    As few events as the text allows, balanced, cut at punctuation when there
    is any. The first version filled each event greedily and left "estava
    indo." alone on screen for under a second.
    """
    words = plain(narration).split()
    if not words:
        return []
    fewest = max(1, -(-len(" ".join(words)) // (CAPTION_LINE * CAPTION_LINES)))
    for count in range(fewest, len(words) + 1):
        events = _split(words, count)
        if events:
            return ["\n".join(_wrap(event)) for event in events]
    # Only a single word longer than two lines (a URL) gets here.
    return ["\n".join(_wrap(word)[:CAPTION_LINES]) for word in words]


def plan(spec: VideoSpec, audio_seconds: float | None = None) -> tuple[Timeline, list[str]]:
    """Durations and caption cues for every scene, plus timing warnings.

    Without a voiceover, each scene lasts as long as its text takes to read.
    With one, the same proportions are stretched or squeezed to the length of
    the recording, because the voice sets the pace and the picture follows it.
    """
    warnings: list[str] = []
    durations = [natural_duration(scene) for scene in spec.scenes]

    if audio_seconds:
        factor = audio_seconds / sum(durations)
        durations = [duration * factor for duration in durations]
        if factor < 0.6:
            warnings.append(
                f"the voiceover ({audio_seconds:.1f}s) is much shorter than the "
                "time the scenes need to be read; the text will flash past."
            )
        elif factor > 1.8:
            warnings.append(
                f"the voiceover ({audio_seconds:.1f}s) is much longer than the "
                "scenes need; they will sit still for a long time."
            )
        rushed = [str(i) for i, d in enumerate(durations, start=1) if d < 1.5]
        if rushed:
            warnings.append(
                f"scene(s) {', '.join(rushed)} last under 1.5s with this voiceover; "
                "nobody reads a slide that fast."
            )

    scenes: list[ScenePlan] = []
    clock = 0.0
    for index, (scene, duration) in enumerate(zip(spec.scenes, durations), start=1):
        scene_plan = ScenePlan(index=index, start=clock, duration=duration)
        if scene.narration:
            events = split_caption(scene.narration)
            weights = [max(1, len(event)) for event in events]
            cursor = clock
            for event, weight in zip(events, weights):
                length = duration * weight / sum(weights)
                end = cursor + min(length, CAPTION_MAX_SECONDS)
                scene_plan.cues.append(Cue(start=cursor, end=end, text=event))
                if length < CAPTION_MIN_SECONDS:
                    warnings.append(
                        f"scene {index}: a caption stays {length:.2f}s on screen, "
                        "under the 5/6 of a second a reader needs. Lengthen the "
                        "scene or cut the narration."
                    )
                elif len(event.replace("\n", " ")) / length > READING_CPS * 1.2:
                    warnings.append(
                        f"scene {index}: a caption runs faster than 17 characters "
                        "per second. Lengthen the scene or cut the narration."
                    )
                cursor += length
        scenes.append(scene_plan)
        clock += duration

    timeline = Timeline(scenes)
    if timeline.total > VIDEO_WARN_SECONDS:
        warnings.append(
            f"the video runs {timeline.total:.0f}s. For a LinkedIn personal profile, "
            f"past {VIDEO_WARN_SECONDS}s video is fighting the format; cut scenes."
        )
    return timeline, warnings


def srt_time(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, rest = divmod(millis, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def to_srt(timeline: Timeline) -> str:
    """The captions as SubRip, the file LinkedIn takes with an uploaded video."""
    blocks = [
        f"{number}\n{srt_time(cue.start)} --> {srt_time(cue.end)}\n{cue.text}\n"
        for number, cue in enumerate(timeline.cues, start=1)
    ]
    return "\n".join(blocks)


# ffmpeg

_DURATION = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def ffmpeg_executable() -> str:
    """The ffmpeg bundled with `imageio-ffmpeg`: no system install needed."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def media_seconds(path: Path) -> float | None:
    """Duration of an audio or video file, read from ffmpeg's own report."""
    completed = subprocess.run(
        [ffmpeg_executable(), "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = _DURATION.search(completed.stderr)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _encode(
    frames: list[tuple[Path, float]],
    target: Path,
    *,
    fps: int,
    total: float,
    voice: Path | None,
) -> str | None:
    """Frames and holds -> H.264 MP4. Returns ffmpeg's error, or None."""
    folder = frames[0][0].parent
    listing = ["ffconcat version 1.0"]
    for path, seconds in frames:
        listing.append(f"file '{path.name}'")
        listing.append(f"duration {seconds:.6f}")
    # The concat demuxer ignores the last entry's duration unless the file is
    # listed once more.
    listing.append(f"file '{frames[-1][0].name}'")
    concat = folder / "frames.ffconcat"
    concat.write_text("\n".join(listing) + "\n", encoding="utf-8")

    fade_start = max(0.0, total - FADE_OUT_SECONDS)
    command = [
        ffmpeg_executable(), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat.name,
    ]
    if voice:
        command += ["-i", str(voice)]
    command += [
        "-vf", f"fps={fps},format=yuv420p,fade=t=out:st={fade_start:.3f}:d={FADE_OUT_SECONDS}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-movflags", "+faststart",
    ]
    if voice:
        command += [
            "-c:a", "aac", "-b:a", "160k",
            "-af", f"afade=t=out:st={fade_start:.3f}:d={FADE_OUT_SECONDS}",
            "-shortest",
        ]
    else:
        command += ["-an"]
    command += ["-t", f"{total:.3f}", str(target.resolve())]

    completed = subprocess.run(
        command, capture_output=True, text=True, cwd=folder, encoding="utf-8", errors="replace"
    )
    if completed.returncode != 0:
        return (completed.stderr or "ffmpeg failed with no output").strip()[-800:]
    return None


# Rendering


@dataclass
class VideoResult:
    out_dir: Path
    ok: bool = False
    video: Path | None = None
    captions: Path | None = None
    cover: Path | None = None
    contact_sheet: Path | None = None
    spec_file: Path | None = None
    duration: float = 0.0
    size: tuple[int, int] = (0, 0)
    fps: int = 30
    voiced: bool = False
    cue_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self, root: Path) -> str:
        def show(path: Path) -> str:
            try:
                return path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                return str(path)

        lines: list[str] = []
        if self.ok and self.video:
            width, height = self.size
            sound = "with the voiceover" if self.voiced else "silent, made to be read muted"
            lines.append(
                f"Video: {show(self.video)} ({width}x{height}, {self.duration:.1f}s, "
                f"{self.fps}fps, {sound})"
            )
            if self.captions:
                lines.append(f"Captions: {show(self.captions)} ({self.cue_count} cues, upload it with the video)")
            else:
                lines.append("Captions: none, because no scene has narration.")
            if self.cover:
                lines.append(f"Cover frame: {show(self.cover)}")
            if self.contact_sheet:
                lines.append(f"Contact sheet: {show(self.contact_sheet)}")
        else:
            lines.append(f"NOT RENDERED. {len(self.errors)} problem(s) to fix first:")
            lines.extend(f"- {error}" for error in self.errors)
        if self.spec_file:
            lines.append(f"Spec: {show(self.spec_file)}")
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


def render_video(
    spec: VideoSpec,
    out_dir: Path,
    *,
    author: Author | None = None,
    content_root: Path | None = None,
    save_spec: bool = True,
) -> VideoResult:
    """Render a video spec to MP4, SRT, a cover frame and a contact sheet.

    `save_spec` writes the normalized spec next to the video. A re-render of a
    spec the user edited by hand passes False, so their comments survive.
    """
    content_root = content_root or CONTENT_DIR
    author = spec.author or author
    width, height = VIDEO_SIZES[spec.aspect]
    result = VideoResult(out_dir=out_dir, size=(width, height), fps=spec.fps)

    out_dir.mkdir(parents=True, exist_ok=True)
    result.spec_file = out_dir / "video.yaml"
    if save_spec:
        result.spec_file.write_text(dump_spec(spec), encoding="utf-8")
    result.errors.extend(text_errors(spec))
    result.warnings.extend(lint(spec))

    voice: Path | None = None
    audio_seconds: float | None = None
    if spec.voiceover:
        voice = confine(content_root, spec.voiceover)
        if voice is None or not voice.is_file():
            result.errors.append(f"voiceover '{spec.voiceover}' was not found under content/.")
            voice = None
        elif voice.suffix.lower() not in AUDIO_EXTENSIONS:
            result.errors.append(
                f"voiceover '{spec.voiceover}' is not an audio file "
                f"({', '.join(sorted(AUDIO_EXTENSIONS))})."
            )
            voice = None
        else:
            audio_seconds = media_seconds(voice)
            if not audio_seconds:
                result.errors.append(f"could not read the length of '{spec.voiceover}'.")

    timeline, timing_warnings = plan(spec, audio_seconds)
    result.warnings.extend(timing_warnings)

    burn = spec.burn_captions and bool(timeline.cues)
    document = build_document(
        spec,
        width=width,
        height=height,
        content_root=content_root,
        author=author,
        mode="video",
        captions=burn,
        resolve_avatar=resolve_asset_path,
    )
    result.errors.extend(document.missing)
    result.warnings.extend(document.redactions)
    if result.errors:
        return result

    def draw_and_encode() -> None:
        with tempfile.TemporaryDirectory(prefix="studio-video-") as scratch:
            folder = Path(scratch)
            frames: list[tuple[Path, float]] = []
            holds: list[Path] = []

            with Studio() as studio:
                page = studio.open_document(document)
                errors, warnings = fit_problems(page.evaluate(FIT_SCRIPT), "scene")
                result.errors.extend(errors)
                result.warnings.extend(warnings)
                if result.errors:
                    return
                slides = page.locator(".slide")

                for scene in timeline.scenes:
                    element = slides.nth(scene.index - 1)

                    def seek(ms: float, caption: str) -> None:
                        page.evaluate(
                            SEEK_SCRIPT,
                            {"index": scene.index - 1, "ms": ms, "caption": caption if burn else ""},
                        )

                    count = max(1, round(min(ENTRANCE_SECONDS, scene.duration / 2) * spec.fps))
                    entrance = count / spec.fps
                    for frame in range(count):
                        moment = frame / spec.fps
                        seek(moment * 1000, scene.caption_at(scene.start + moment))
                        path = folder / f"s{scene.index:02d}-f{frame:03d}.png"
                        element.screenshot(path=str(path))
                        frames.append((path, 1 / spec.fps))

                    # The hold is split wherever a caption starts or ends, so
                    # each piece is one screenshot with the right caption on it.
                    marks = {entrance, scene.duration}
                    for cue in scene.cues:
                        marks.update({cue.start - scene.start, cue.end - scene.start})
                    ordered = sorted(m for m in marks if entrance <= m <= scene.duration)
                    for piece, (begin, finish) in enumerate(zip(ordered, ordered[1:])):
                        if finish - begin < 0.001:
                            continue
                        seek(60_000, scene.caption_at(scene.start + begin + 0.0005))
                        path = folder / f"s{scene.index:02d}-h{piece:02d}.png"
                        element.screenshot(path=str(path))
                        frames.append((path, finish - begin))
                        if piece == 0:
                            holds.append(path)

            video = out_dir / "video.mp4"
            failure = _encode(
                frames, video, fps=spec.fps, total=timeline.total, voice=voice
            )
            if failure:
                result.errors.append(f"ffmpeg could not encode the video: {failure}")
                return

            result.video = video
            result.voiced = voice is not None
            result.duration = media_seconds(video) or timeline.total
            result.cover = out_dir / "cover.png"
            shutil.copyfile(holds[0], result.cover)
            result.contact_sheet = make_contact_sheet(holds, out_dir / "contact-sheet.png")

            captions = out_dir / "captions.srt"
            if timeline.cues:
                captions.write_text(to_srt(timeline), encoding="utf-8")
                result.captions = captions
                result.cue_count = len(timeline.cues)
            elif captions.exists():
                captions.unlink()
            result.ok = True

    run_isolated(draw_and_encode)
    return result
