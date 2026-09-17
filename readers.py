from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class DocumentResult:
    path: str
    kind: str
    renderer: str
    support: str

    content: Any = None
    metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


READERS: dict[str, Callable] = {}


def reader(*formats):
    def decorator(fn):
        for fmt in formats:
            READERS[fmt] = fn
        return fn

    return decorator


# ── Magic bytes signatures ────────────────────────────────────────────────

SIGNATURES: dict[bytes, str] = {
    b"%PDF": "pdf",
    b"\x89PNG\r\n\x1a\n": "png",
    b"\xff\xd8\xff": "jpeg",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"PK\x03\x04": "zip-container",
    b"Rar!\x1a\x07": "rar",
    b"7z\xbc\xaf\x27\x1c": "7z",
}


def sniff_header(path: str) -> str | None:
    """Identify format by reading the first 32 bytes (magic bytes)."""
    with open(path, "rb") as f:
        header = f.read(32)

    for signature, kind in SIGNATURES.items():
        if header.startswith(signature):
            return kind
    return None


# ── OOXML container inspection ─────────────────────────────────────────────

def detect_ooxml(path: str) -> str | None:
    """Look inside a ZIP container to determine Office format."""
    import zipfile

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())

            if "word/document.xml" in names:
                return "docx"
            if "xl/workbook.xml" in names:
                return "xlsx"
            if "ppt/presentation.xml" in names:
                return "pptx"

            # EPUB is also a ZIP with specific structure
            if "mimetype" in names:
                mimetype = archive.read("mimetype").decode("utf-8", errors="replace").strip()
                if mimetype == "application/epub+zip":
                    return "epub"

    except zipfile.BadZipFile:
        return None

    return "zip"


# ── Text reader ────────────────────────────────────────────────────────────

@reader("txt", "log", "md", "json", "py", "js", "ts", "tsx", "jsx")
def read_text(path: str) -> DocumentResult:
    text = Path(path).read_text(
        encoding="utf-8",
        errors="replace",
    )

    return DocumentResult(
        path=str(path),
        kind="text",
        renderer="text",
        support="L1",
        content=text,
        metadata={
            "encoding": "utf-8",
            "line_count": text.count("\n") + 1 if text else 0,
        },
    )


# ── PDF reader (via Qt QPdfDocument) ──────────────────────────────────────

@reader("pdf")
def read_pdf(path: str) -> DocumentResult:
    # TODO: Implement when Qt PDF module is available
    # For now, fall back to text extraction via magic bytes
    text = Path(path).read_text(encoding="utf-8", errors="replace")[:500]

    return DocumentResult(
        path=str(path),
        kind="pdf",
        renderer="pdf",
        support="L1",
        content=f"[PDF via Qt] {text}" if text else "[PDF document - full render via QPdfView]",
        metadata={},
        warnings=["PDF full rendering depends on Qt QPdfView availability"],
    )


# ── DOCX via Mammoth ──────────────────────────────────────────────────────

@reader("docx")
def read_docx(path: str) -> DocumentResult:
    try:
        import mammoth

        with open(path, "rb") as f:
            result = mammoth.convert_to_html(f)

        html = result.value
        messages = result.messages or []

        # Simple warning collection from mammoth messages
        warnings = []
        for msg in messages:
            warnings.append(str(msg))

        return DocumentResult(
            path=str(path),
            kind="docx",
            renderer="html",
            support="L2",
            content=html,
            metadata={
                " mammoth_messages": len(messages),
            },
            warnings=warnings or None,
        )
    except Exception as e:
        return DocumentResult(
            path=str(path),
            kind="docx",
            renderer="html",
            support="L3",
            content=None,
            metadata={},
            warnings=[f"DOCX conversion failed: {e}"],
        )


# ── XLSX via openpyxl ─────────────────────────────────────────────────────

@reader("xlsx")
def read_xlsx(path: str) -> DocumentResult:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)

        # Build a simple text representation
        rows: list[list[str]] = []
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_rows: list[list[str]] = []
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=ws.max_column):
                sheet_rows.append(
                    [str(cell.value) if cell is not None else "" for cell in row]
                )
            rows.append(f"=== Sheet: {sheet_name} ===")
            rows.extend(sheet_rows)

        wb.close()

        content = "\n".join(rows) if rows else "(empty workbook)"

        return DocumentResult(
            path=str(path),
            kind="xlsx",
            renderer="spreadsheet",
            support="L1",
            content=content,
            metadata={
                "sheet_count": len(wb.sheetnames),
                "max_row": wb.properties.lastSaved if wb.properties else None,
            },
        )
    except Exception as e:
        return DocumentResult(
            path=str(path),
            kind="xlsx",
            renderer="spreadsheet",
            support="L3",
            content=None,
            metadata={},
            warnings=[f"XLSX read failed: {e}"],
        )


# ── ZIP / Archive inspector ───────────────────────────────────────────────

@reader("zip", "tar", "gz", "7z", "rar")
def read_archive(path: str) -> DocumentResult:
    import zipfile
    import tarfile
    import os

    path_obj = Path(path)
    name = path_obj.name
    size = path_obj.stat().st_size

    entries: list[str] = []
    metadata: dict[str, Any] = {}

    try:
        if path.endswith(".zip"):
            with zipfile.ZipFile(path) as z:
                entries = z.namelist()
                metadata = {
                    "compressed_size": z.file_size,
                    "uncompressed_size": z.testzip(),
                    "entry_count": len(z.namelist()),
                }
        elif path.endswith((".tar", ".gz")):
            with tarfile.open(path) as t:
                entries = t.getnames()
                metadata = {
                    "entry_count": len(entries),
                }
        elif path.endswith(".7z"):
            # 7z support would require py7zr; fall back to inspecting header
            entries = ["(7z support pending - binary inspection)"]
            metadata = {"format": "7z", "note": "Requires py7zr for full inspection"}
        elif path.endswith(".rar"):
            entries = ["(RAR support pending - binary inspection)"]
            metadata = {"format": "rar", "note": "Requires unrar for full inspection"}

        # Truncate if too many entries
        if len(entries) > 50:
            metadata["truncated"] = True
            entries = entries[:50] + [f"… + {len(entries) - 50} more"]

        content_text = (
            f"Archive: {name}\n"
            f"Size: {size} bytes\n"
            f"Entries: {len(entries)}\n\n"
            + "\n".join(entries[:20])
        )

        support = "L3" if path.endswith(".zip") else "L4"

        return DocumentResult(
            path=str(path),
            kind="archive",
            renderer="archive",
            support=support,
            content=content_text,
            metadata=metadata,
            warnings=None,
        )

    except (zipfile.BadZipFile, tarfile.TarError) as e:
        # Fall back to hex inspection
        return read_unknown(path, f"Archive corrupted: {e}")


# ── Unknown / binary inspector ────────────────────────────────────────────

def read_unknown(path: str, hint: str = "") -> DocumentResult:
    p = Path(path)
    data = p.read_bytes()

    # Extract readable strings
    strings: list[str] = []
    current: bytearray = bytearray()
    for byte in data:
        if 32 <= byte < 127:
            current.append(byte)
        else:
            if len(current) >= 4:
                strings.append(current.decode("ascii", errors="replace"))
            current = bytearray()
    if len(current) >= 4:
        strings.append(current.decode("ascii", errors="replace"))

    # Compute entropy (simple version)
    from collections import Counter
    if data:
        counts = Counter(data)
        length = len(data)
        entropy = -sum((c / length) * __import__("math").log2(c / length) for c in counts.values())
    else:
        entropy = 0

    hex_preview = " ".join(f"{b:02x}" for b in data[:64])

    content = (
        f"Unknown format\n"
        f"File: {p.name}\n"
        f"Size: {len(data)} bytes\n"
        f"Entropy: {entropy:.2f}\n\n"
        f"Magic bytes (first 32): {hex_preview}\n\n"
        f"Detected strings:\n" + "\n".join(f"  • {s}" for s in strings[:20])
        + ("\n\n" + hint if hint else "")
    )

    return DocumentResult(
        path=str(path),
        kind="unknown",
        renderer="hex",
        support="L4",
        content=content,
        metadata={
            "entropy": round(entropy, 2),
            "file_size": len(data),
            "string_count": len(strings),
        },
        warnings=[hint] if hint else None,
    )


# ── Main dispatcher ────────────────────────────────────────────────────────

def open_document(path: str) -> DocumentResult:
    """Detect format and return a DocumentResult with the appropriate reader."""

    path = str(path)
    p = Path(path)

    if not p.exists():
        return DocumentResult(
            path=path,
            kind="error",
            renderer="none",
            support="L4",
            content=None,
            metadata={},
            warnings=[f"File not found: {path}"],
        )

    # 1. Try header/magic bytes detection
    kind = sniff_header(path)

    # 2. If ZIP container, inspect internal structure
    if kind == "zip-container":
        kind = detect_ooxml(path)

    # 3. Try registered reader by detected kind
    reader_fn = READERS.get(kind)

    if reader_fn:
        try:
            return reader_fn(path)
        except Exception as e:
            return DocumentResult(
                path=path,
                kind=kind or "unknown",
                renderer=kind or "unknown",
                support="L3",
                content=None,
                metadata={},
                warnings=[f"Reader error: {e}"],
            )

    # 4. Fallback: text detection when no magic-byte kind matched
    # If we don't have a recognized format, try reading as text.
    # We use a lenient check: attempt UTF-8 decode; if the file is mostly
    # printable/readable content, treat it as text.
    if not kind:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="strict")
            # If we got here with strict mode, it's valid UTF-8.
            # But allow files with minor replacement-character issues too:
            # (if errors="replace" would work, that's also OK for preview purposes)
            return read_text(path)
        except (UnicodeDecodeError, ValueError):
            # Not pure UTF-8; try with replacement (lenient)
            try:
                text = Path(path).read_text(encoding="utf-8", errors="replace")
                # Only accept if the replaced content isn't too different
                # i.e., replacement characters are a small fraction
                replaced = Path(path).read_text(encoding="utf-8", errors="replace")
                original_bytes = Path(path).read_bytes()
                # Count bytes that were replaced (rough heuristic)
                # If more than 20% of bytes needed replacement, reject
                try:
                    original_text = Path(path).read_text(encoding="utf-8", errors="ignore")
                    # Very rough: compare lengths
                    if len(replaced) > len(original_text) * 0.8:
                        return read_text(path)
                except Exception:
                    return read_text(path)
            except Exception:
                pass

    # 5. If we have a kind but no registered reader, try text fallback
    if kind and kind not in READERS:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="strict")
            return read_text(path)
        except (UnicodeDecodeError, ValueError):
            try:
                text = Path(path).read_text(encoding="utf-8", errors="replace")
                return read_text(path)
            except Exception:
                pass

    # 6. Last resort: unknown inspector
    return read_unknown(path)


# ── Convenience: detect support level string ───────────────────────────────

SUPPORT_LEVELS = {
    "L1": "Native — renderização nativa",
    "L2": "Converted — convertido para HTML/PDF",
    "L3": "Extracted — conteúdo extraído",
    "L4": "Inspected — análise hex/strings/metadata",
}


def support_level_name(level: str) -> str:
    return SUPPORT_LEVELS.get(level, "Unknown level")