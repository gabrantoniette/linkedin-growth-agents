"""Any supported file becomes a PDF LinkedIn accepts as a document post.

Converting is the faithful path: the file's own content, set in the studio's
typography, on 1080x1350 pages. It is not the designed path. A carousel is an
argument compressed into slides, one idea each, and that is the Post Designer's
job with a spec. Converting is for when the content already exists and only has
to become a document: a study note, a README, a spreadsheet, a deck made
elsewhere, a batch of screenshots.

What goes in, and how it comes out:

    .md .markdown .mdx          markdown, typeset; code fences highlighted
    .txt .log                   plain text, typeset
    .html .htm                  printed as the page itself
    .docx                       read with mammoth, typeset like markdown
    .csv .tsv                   a table whose header repeats on every page
    source code (.py .ts ...)   highlighted, any extension Pygments knows
    .png .jpg .webp .gif .bmp   one image per page, fitted
    .pdf                        kept as-is when its pages share one size,
                                refit onto 1080x1350 when they do not
    .pptx .ppt .odp .odt .doc   through LibreOffice, when it is installed
    .rtf .xlsx .xls .ods

Two LinkedIn rules shape the output (kb-visual-formats.md §3.1): every page of
a document must share one size, and a document may not pass 300 pages or 100MB.
The first is guaranteed here; the second is reported.

Text that goes through the typesetter is redacted first, exactly like a code
slide (see `safety.py`): a key pasted into a study note is a key in a public
PDF.
"""

from __future__ import annotations

import csv
import html as html_escape
import io
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from markupsafe import Markup
from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

from linkedin_growth.config import TMP_DIR
from linkedin_growth.studio.browser import Studio, run_isolated
from linkedin_growth.studio.code import highlight
from linkedin_growth.studio.html import ORIGIN, Document, font_faces, render_template
from linkedin_growth.studio.safety import confine, redact_secrets
from linkedin_growth.studio.spec import Author
from linkedin_growth.studio.themes import CAROUSEL_SIZE, get_theme

LINKEDIN_MAX_PAGES = 300
LINKEDIN_MAX_BYTES = 100 * 1024 * 1024
MAX_TABLE_ROWS = 2000
OFFICE_TIMEOUT_SECONDS = 180

KINDS: dict[str, set[str]] = {
    "markdown": {".md", ".markdown", ".mdx"},
    "text": {".txt", ".text", ".log"},
    "html": {".html", ".htm"},
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"},
    "pdf": {".pdf"},
    "docx": {".docx"},
    "table": {".csv", ".tsv"},
    "office": {".pptx", ".ppt", ".odp", ".odt", ".doc", ".rtf", ".xlsx", ".xls", ".ods"},
}


def kind_of(path: Path) -> str | None:
    """Which converter handles a file, by extension. None when nothing does."""
    suffix = path.suffix.lower()
    for kind, suffixes in KINDS.items():
        if suffix in suffixes:
            return kind
    try:
        get_lexer_for_filename(path.name)
    except ClassNotFound:
        return None
    return "code"


def supported_extensions() -> str:
    listed = sorted(suffix for suffixes in KINDS.values() for suffix in suffixes)
    return ", ".join(listed) + ", and source code Pygments recognizes"


@dataclass
class ConvertResult:
    source: Path
    ok: bool = False
    pdf: Path | None = None
    kind: str | None = None
    pages: int = 0
    page_size_pt: tuple[float, float] = (0.0, 0.0)
    size_bytes: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self, root: Path) -> str:
        def show(path: Path) -> str:
            try:
                return path.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                return str(path)

        if not self.ok or not self.pdf:
            lines = [f"NOT CONVERTED ({self.source.name}):"]
            lines.extend(f"- {error}" for error in self.errors)
        else:
            width, height = self.page_size_pt
            megabytes = self.size_bytes / (1024 * 1024)
            lines = [
                f"PDF: {show(self.pdf)} ({self.pages} pages, {width:.0f}x{height:.0f}pt, "
                f"{megabytes:.1f}MB), converted from {self.source.name} as {self.kind}",
            ]
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


# Building the HTML


def _redacted(text: str, result: ConvertResult) -> str:
    cleaned, found = redact_secrets(text)
    if found:
        result.warnings.append(
            f"masked {len(found)} credential-looking value(s) before typesetting: "
            + ", ".join(sorted(set(found)))
        )
    return cleaned


def _code_block(code: str, language: str | None = None, filename: str | None = None) -> str:
    highlighted = highlight(code, language=language, filename=filename)
    lines = "".join(
        f'<span class="code-line">{line.html}</span>' for line in highlighted.lines
    )
    return f'<pre class="block"><code>{lines}</code></pre>\n'


def _page(
    body: str,
    *,
    label: str,
    title: str,
    theme: str,
    language: str,
    author: Author | None,
    files: dict[str, Path] | None = None,
) -> Document:
    chosen = get_theme(theme)
    width, height = CAROUSEL_SIZE
    html = render_template(
        "document.html.j2",
        title=title,
        label=label,
        body=Markup(body),
        author=author,
        language=language,
        theme_id=chosen.id,
        theme_vars=Markup(chosen.css_variables()),
        font_faces=font_faces(),
        width=width,
        height=height,
    )
    return Document(html=html, files=files or {}, width=width, height=height, count=0)


def _first_heading(markdown: str) -> str | None:
    match = re.search(r"^#{1,2}\s+(.+?)\s*#*\s*$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else None


def _markdown(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    from markdown_it import MarkdownIt

    text = _redacted(source.read_text(encoding="utf-8", errors="replace"), result)

    # `html: False` escapes any raw HTML in the file instead of rendering it.
    renderer = MarkdownIt(
        "commonmark",
        {"html": False, "highlight": lambda code, lang, _attrs: _code_block(code, lang or None)},
    ).enable(["table", "strikethrough"])

    tokens = renderer.parse(text)
    files: dict[str, Path] = {}
    for token in tokens:
        for child in token.children or []:
            if child.type != "image":
                continue
            src = str(child.attrGet("src") or "")
            if re.match(r"^[a-z][a-z0-9+.\-]*:", src, re.IGNORECASE):
                # Remote images are never fetched; the render reports them.
                continue
            target = confine(source.parent, src)
            if target and target.is_file():
                token_name = f"doc-{len(files) + 1}{target.suffix.lower()}"
                files[token_name] = target
                child.attrSet("src", f"{ORIGIN}/files/{token_name}")
    body = renderer.renderer.render(tokens, renderer.options, {})
    title = _first_heading(text) or source.stem
    return _page(body, label=source.name, title=title, theme=theme, language=language, author=author, files=files)


def _text(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    text = _redacted(source.read_text(encoding="utf-8", errors="replace"), result)
    body = f'<pre class="plain">{html_escape.escape(text, quote=False)}</pre>'
    return _page(body, label=source.name, title=source.stem, theme=theme, language=language, author=author)


def _code(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    text = _redacted(source.read_text(encoding="utf-8", errors="replace"), result)
    body = _code_block(text, filename=source.name)
    return _page(body, label=source.name, title=source.name, theme=theme, language=language, author=author)


def _docx(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    import mammoth

    with source.open("rb") as handle:
        converted = mammoth.convert_to_html(handle)
    body = _redacted(converted.value, result)
    # Only web and mail links survive; anything else becomes inert.
    body = re.sub(r'href="(?!https?:|mailto:|#)[^"]*"', 'href="#"', body)
    for message in converted.messages[:5]:
        result.warnings.append(f"from the .docx reader: {message.message}")
    return _page(body, label=source.name, title=source.stem, theme=theme, language=language, author=author)


def _table(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    raw = _redacted(source.read_text(encoding="utf-8-sig", errors="replace"), result)
    if source.suffix.lower() == ".tsv":
        delimiter = "\t"
    else:
        try:
            delimiter = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t|").delimiter
        except csv.Error:
            delimiter = ","
    rows = [row for row in csv.reader(io.StringIO(raw), delimiter=delimiter) if row]
    if not rows:
        return _page("<p>(empty file)</p>", label=source.name, title=source.stem, theme=theme, language=language, author=author)

    header, body_rows = rows[0], rows[1:]
    if len(body_rows) > MAX_TABLE_ROWS:
        result.warnings.append(
            f"the table has {len(body_rows)} rows; only the first {MAX_TABLE_ROWS} were typeset."
        )
        body_rows = body_rows[:MAX_TABLE_ROWS]

    def cells(row: list[str], tag: str) -> str:
        return "".join(f"<{tag}>{html_escape.escape(cell, quote=False)}</{tag}>" for cell in row)

    body = (
        "<table><thead><tr>" + cells(header, "th") + "</tr></thead><tbody>"
        + "".join(f"<tr>{cells(row, 'td')}</tr>" for row in body_rows)
        + "</tbody></table>"
    )
    return _page(body, label=source.name, title=source.stem, theme=theme, language=language, author=author)


def _html(source: Path, result: ConvertResult, theme: str, language: str, author: Author | None) -> Document:
    width, height = CAROUSEL_SIZE
    result.warnings.append(
        "the page is printed offline: anything it loads from the internet (fonts, "
        "images, scripts) is left out."
    )
    return Document(
        html=source.read_text(encoding="utf-8", errors="replace"),
        files={},
        width=width,
        height=height,
        count=0,
        base_dir=source.parent,
    )


def _images(paths: list[Path], *, theme: str, language: str, title: str, captions: bool, bleed: bool) -> Document:
    chosen = get_theme(theme)
    width, height = CAROUSEL_SIZE
    files = {f"image-{index}{path.suffix.lower()}": path for index, path in enumerate(paths, start=1)}
    images = [
        {"src": f"{ORIGIN}/files/{token}", "caption": path.name if captions else ""}
        for token, path in files.items()
    ]
    html = render_template(
        "images.html.j2",
        title=title,
        language=language,
        images=images,
        bleed=bleed,
        theme_vars=Markup(chosen.css_variables()),
        font_faces=font_faces(),
        width=width,
        height=height,
    )
    return Document(html=html, files=files, width=width, height=height, count=len(paths))


# Printing

_WAIT_FOR_ASSETS = """async () => {
  await document.fonts.ready;
  const images = [...document.images];
  await Promise.all(images.map((img) => img.complete ? null : new Promise((done) => { img.onload = img.onerror = done; })));
  return images.filter((img) => !img.naturalWidth).map((img) => img.getAttribute('src'));
}"""


def _print(document: Document, target: Path, result: ConvertResult, *, prefer_css_page_size: bool = False) -> None:
    def work() -> None:
        with Studio() as studio:
            page = studio.open_document(document)
            broken = page.evaluate(_WAIT_FOR_ASSETS)
            if broken:
                result.warnings.append(
                    f"{len(broken)} image(s) could not be loaded and are missing "
                    "from the PDF (remote images are never fetched)."
                )
            page.pdf(
                path=str(target),
                width=f"{document.width}px",
                height=f"{document.height}px",
                print_background=True,
                prefer_css_page_size=prefer_css_page_size,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )

    run_isolated(work)
    result.pdf = target


def _page_sizes(pdf: Path) -> list[tuple[float, float]]:
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(str(pdf))
    try:
        return [tuple(round(value, 1) for value in document[index].get_size()) for index in range(len(document))]
    finally:
        document.close()


def _pdf(source: Path, target: Path, result: ConvertResult, theme: str, language: str) -> None:
    """Keep a PDF whose pages share one size; refit one whose pages do not."""
    import pypdfium2 as pdfium

    sizes = _page_sizes(source)
    if len(set(sizes)) <= 1:
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        result.pdf = target
        return

    with tempfile.TemporaryDirectory(prefix="studio-pdf-") as scratch:
        document = pdfium.PdfDocument(str(source))
        paths: list[Path] = []
        try:
            for index in range(len(document)):
                page = document[index]
                page_width, _ = page.get_size()
                scale = min(3.0, 2160 / max(page_width, 1.0))
                path = Path(scratch) / f"page-{index + 1:03d}.png"
                page.render(scale=scale).to_pil().save(path)
                paths.append(path)
        finally:
            document.close()
        _print(
            _images(paths, theme=theme, language=language, title=source.stem, captions=False, bleed=True),
            target,
            result,
        )
    result.warnings.append(
        "the pages had different sizes, which LinkedIn does not accept in a "
        "document; they were refit onto 1080x1350 pages as images, so their text "
        "is no longer selectable."
    )


def find_libreoffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for candidate in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


def _office(source: Path, target: Path, result: ConvertResult, theme: str, language: str) -> None:
    soffice = find_libreoffice()
    if not soffice:
        result.errors.append(
            f"{source.suffix} files are converted through LibreOffice, which is not "
            "installed. Install it (on Windows: winget install "
            "TheDocumentFoundation.LibreOffice; elsewhere: https://www.libreoffice.org), "
            "or export the file to PDF from the app that made it and convert that PDF "
            "instead."
        )
        return
    # A profile of its own, under tmp/. A headless conversion that shares the
    # desktop profile is handed to the LibreOffice already open, and can return
    # without converting anything.
    profile = (TMP_DIR / "libreoffice-profile").resolve()
    profile.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="studio-office-") as scratch:
        try:
            completed = subprocess.run(
                [
                    soffice,
                    f"-env:UserInstallation={profile.as_uri()}",
                    "--headless",
                    "--norestore",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    scratch,
                    str(source),
                ],
                capture_output=True,
                text=True,
                timeout=OFFICE_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            result.errors.append(f"LibreOffice took over {OFFICE_TIMEOUT_SECONDS}s and was stopped.")
            return
        produced = Path(scratch) / f"{source.stem}.pdf"
        if completed.returncode != 0 or not produced.is_file():
            detail = (completed.stderr or completed.stdout or "").strip()[-300:]
            result.errors.append(f"LibreOffice could not convert the file. {detail}".strip())
            return
        _pdf(produced, target, result, theme, language)


_TYPESET: dict[str, Callable[..., Document]] = {
    "markdown": _markdown,
    "text": _text,
    "code": _code,
    "docx": _docx,
    "table": _table,
    "html": _html,
}


def convert_file(
    source: Path,
    target: Path,
    *,
    theme: str = "drafting",
    language: str = "pt-BR",
    author: Author | None = None,
) -> ConvertResult:
    """Convert `source` into the PDF at `target`."""
    result = ConvertResult(source=source)
    if not source.is_file():
        result.errors.append(f"'{source}' does not exist or is not a file.")
        return result

    result.kind = kind_of(source)
    if result.kind is None:
        result.errors.append(
            f"'{source.suffix or source.name}' is not a type the studio converts. "
            f"Supported: {supported_extensions()}."
        )
        return result

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        if result.kind == "pdf":
            _pdf(source, target, result, theme, language)
        elif result.kind == "office":
            _office(source, target, result, theme, language)
        elif result.kind == "image":
            _print(
                _images([source], theme=theme, language=language, title=source.stem, captions=False, bleed=False),
                target,
                result,
            )
        else:
            document = _TYPESET[result.kind](source, result, theme, language, author)
            _print(document, target, result, prefer_css_page_size=result.kind == "html")
    except (OSError, UnicodeError, ValueError) as error:
        result.errors.append(f"could not read or write the file: {error}")

    if result.errors or not result.pdf or not result.pdf.is_file():
        return result

    sizes = _page_sizes(result.pdf)
    result.pages = len(sizes)
    result.page_size_pt = sizes[0] if sizes else (0.0, 0.0)
    result.size_bytes = result.pdf.stat().st_size
    if len(set(sizes)) > 1:
        result.warnings.append("the output still has pages of different sizes; LinkedIn will reject it.")
    if result.pages > LINKEDIN_MAX_PAGES:
        result.warnings.append(f"{result.pages} pages: LinkedIn accepts at most {LINKEDIN_MAX_PAGES}.")
    if result.size_bytes > LINKEDIN_MAX_BYTES:
        result.warnings.append("over 100MB: LinkedIn will not accept the upload.")
    result.ok = True
    return result
