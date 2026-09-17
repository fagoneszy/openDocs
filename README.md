<p align="center">
  <img src="./OpenDocs.png" width="100%" alt="OpenDocs — One app. Any document.">
</p>

<p align="center">
  <strong>ONE APP. ANY DOCUMENT.</strong>
</p>

<p align="center">
  Universal Document Viewer
</p>

<p align="center">
  <kbd>OPEN SOURCE</kbd>
  <kbd>OFFLINE</kbd>
  <kbd>LOCAL-FIRST</kbd>
  <kbd>CROSS-PLATFORM</kbd>
</p>

<p align="center">
  <sub>v0.1.0 — FIRST LIGHT</sub>
</p>

---

## `> ABOUT_`

OpenDocs is a lightweight, open-source universal document viewer built
around one simple idea:

> **Drop any file into OpenDocs and something useful should happen.**

Instead of requiring a different application for every format, OpenDocs
detects the real file type and selects the best available reader.

When full rendering is not available, it gracefully falls back to content
extraction, metadata analysis, strings or hexadecimal inspection.

```text
FILE
 │
 ├── detected ──────> reader ──────> preview
 │
 └── unknown ───────> inspector ───> metadata / strings / hex
```

---

## `> SYSTEM_STATUS_`

| Property | Status |
|---|---|
| Universal detection | `ONLINE` |
| Offline operation | `ENABLED` |
| Cloud dependency | `NONE` |
| Telemetry | `DISABLED` |
| Automatic macros | `BLOCKED` |
| Unknown-file inspection | `READY` |
| Release | `v0.1.0 First Light` |

---

## `> FEATURES_`

- **Universal detection** — magic bytes + internal structure
- **Native previews** — text, source code, PDF, images and spreadsheets
- **Office support** — DOCX and XLSX
- **Unknown inspector** — metadata, strings and hexadecimal data
- **Drag & drop** — drop a document directly into the application
- **CLI opening** — pass a document when starting OpenDocs
- **Local-first** — documents never need to leave your computer
- **No accounts · No cloud · No telemetry**

---

## `> SUPPORT_LEVELS_`

OpenDocs uses four explicit support levels.

| Level | Mode | Meaning |
|:---:|---|---|
| `L1` | **Native** | Direct/native preview |
| `L2` | **Converted** | Converted before preview |
| `L3` | **Extracted** | Useful content is extracted |
| `L4` | **Inspected** | Raw file analysis |

> OpenDocs does not pretend every format can be rendered perfectly.
>
> **"Any document" means every file should produce something useful.**

---

## `> FORMAT_MATRIX_`

| Level | Format | Renderer |
|:---:|---|---|
| `L1` | PDF | Qt `QPdfView` |
| `L1` | TXT / MD / JSON / Code | Native text |
| `L1` | PNG / JPEG / WebP / GIF / SVG | Qt Image |
| `L1` | XLSX | openpyxl |
| `L2` | DOCX | Mammoth → HTML |
| `L3` | ZIP / archive | Archive inspection |
| `L4` | Unknown | Metadata / strings / hex |

```text
PDF   ████████████████████  L1
TEXT  ████████████████████  L1
IMAGE ████████████████████  L1
XLSX  ████████████████████  L1
DOCX  ████████████████░░░░  L2
ZIP   ████████████░░░░░░░░  L3
???   ████████░░░░░░░░░░░░  L4
```

---

## `> DETECTION_ENGINE_`

OpenDocs does **not** trust the filename alone.

```text
Extension
    │
    ▼
Magic Bytes
    │
    ▼
Internal Structure
    │
    ▼
Format Resolver
    │
    ▼
Reader Registry
```

For example, renaming:

```text
document.pdf → document.txt
```

does not magically turn the PDF into a text file.

OpenDocs inspects the actual content.

---

## `> INSTALLATION_`

### Windows

```powershell
git clone YOUR_REPOSITORY
cd opendocs

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python main.py
```

### Linux / macOS

```bash
git clone YOUR_REPOSITORY
cd opendocs

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

Pre-built binaries are also distributed through GitHub Releases.

---

## `> USAGE_`

Open the application:

```bash
python main.py
```

Open a document directly:

```bash
python main.py document.pdf
```

With the packaged Windows release:

```powershell
OpenDocs.exe document.pdf
```

Or simply:

```text
drag file
    ↓
 OpenDocs
    ↓
 useful output
```

---

## `> ARCHITECTURE_`

OpenDocs intentionally keeps its architecture extremely small.

```text
opendocs/
│
├── main.py
├── readers.py
├── ui.py
├── requirements.txt
├── README.md
├── LICENSE
└── OpenDocs.png
```

Repository infrastructure additionally includes:

```text
.gitignore
```

### `main.py`

Application entry point.

```text
QApplication
     ↓
  OpenDocs
     ↓
 event loop
```

### `readers.py`

The brain of OpenDocs.

```text
detection
registry
readers
DocumentResult
fallback inspector
```

### `ui.py`

The presentation layer.

```text
PySide6
drag & drop
document preview
status information
```

---

## `> ADD_A_FORMAT_`

Adding support for another format should remain intentionally simple:

```python
@reader("abc")
def read_abc(path):
    return DocumentResult(...)
```

That's it.

No plugin framework to learn.

No inheritance tree.

No mandatory base classes.

No internal SDK.

---

## `> SECURITY_`

OpenDocs treats documents as **data**, not executable programs.

| Behavior | Policy |
|---|---|
| JavaScript execution | `BLOCKED` |
| Office macros | `NEVER EXECUTED` |
| Automatic scripts | `BLOCKED` |
| Cloud processing | `NONE` |
| Telemetry | `NONE` |
| File analysis | `LOCAL` |

Your documents stay on your computer.

---

## `> PHILOSOPHY_`

```text
┌───────────────────────────────────────────────────────────┐
│                                                           │
│  If a feature makes OpenDocs significantly harder         │
│  to understand, it probably doesn't belong in OpenDocs.   │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

OpenDocs is intentionally:

**small · readable · hackable · local-first**

A contributor should be able to clone the repository, read the core and
understand how to add a reader without first learning an internal framework.

---

## `> ROADMAP_`

| Release | Target |
|---|---|
| `v0.1` | Detection · PDF · DOCX · XLSX · Text · Images · Inspector |
| `v0.2` | EPUB · ODT · Tabs · Recent documents |
| `v0.3` | Search · Outline · Advanced metadata |
| `v1.0` | Stable format API · Mature extension system |

The roadmap is intentionally conservative.

New features should not compromise the simplicity of the core.

---

## `> RELEASE_`

### OpenDocs `v0.1.0`

**Codename:** `FIRST LIGHT`

```text
BUILD STATUS       READY
OFFLINE MODE       ENABLED
TELEMETRY          DISABLED
CLOUD              NOT REQUIRED
SUPPORT LEVELS     L1 / L2 / L3 / L4
```

---

## `> LICENSE_`

OpenDocs is distributed under the **MIT License**.

See `LICENSE` for the complete license text.

---

<p align="center">
  <strong>OPENDOCS</strong>
</p>

<p align="center">
  <sub>ONE APP. ANY DOCUMENT.</sub>
</p>

<p align="center">
  <sub>OPEN SOURCE · OFFLINE · LOCAL-FIRST</sub>
</p>
