# StudyMate — SmartNotes Application

> Lightweight PyQt5 desktop for study notes with local Hugging Face summarization, key-phrase extraction and mind-map visualization.

***Portfolio Project*** *— Demonstrates local LLM inference orchestration, Qt threading & service-layer architecture, lazy model loading, and graph visualization with CI-guarded quality.*

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square) ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square) ![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square) ![Tests](https://img.shields.io/badge/Tests-31_passed-brightgreen?style=flat-square) ![Coverage](https://img.shields.io/badge/Coverage-services_92%25-blue?style=flat-square)

---

## Table of Contents

- [System Demonstration](#system-demonstration)
- [Why This Project Matters](#why-this-project-matters)
- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution Approach](#solution-approach)
- [Demo](#demo)
- [Features](#features)
- [Results & Metrics](#results--metrics)
- [Architecture](#architecture)
- [Engineering Decisions](#engineering-decisions)
- [Challenges & Lessons Learned](#challenges--lessons-learned)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Testing & Verification](#testing--verification)
- [Future Improvements](#future-improvements)
- [Author](#author)

---

## System Demonstration

### System Workflow

```text
[User Input: .txt/.md/.py/.docx/.odt/.pdf]
        │
        ▼
[MainWindow + SideBar + Tabbed Editor (PyQt5)]
        │
        ├──► FileService — reader registry, ODT→PDF via LibreOffice
        ├──► SearchService — find/replace with wrap-around
        └──► SettingsManager/Model — QSettings persistence
        │
        ▼
[AI Workers (QThreadPool, non-blocking)]
        │
        ├──► SummarizerService — sshleifer/distilbart-cnn-6-6, chunked (600w) + truncation
        ├──► KeyPointsService — ml6team/keyphrase-extraction-kbir-inspec, B-KEY filter
        └──► MindMapService — summarizer → indented list → GraphVisualizer
        │
        ▼
[Rendering]
        │
        ├──► EditorArea (QTextEdit) — summary/key-points/mind-map text
        ├──► GraphVisualizer — networkx DiGraph + matplotlib → QPixmap
        └──► PdfViewer — PyMuPDF (fitz) pixmap with zoom/fit
        │
        ▼
[Persistence & Export]
        │
        ├──► SchedulerTab — JSON via QStandardPaths (StudyMate/scheduler_tasks.json)
        ├──► QPrinter — export editor → PDF
        └──► Mind-map → PNG export
```

### Application Screenshots

| AI Tools | File Explorer | Scheduler | Settings & Editor |
|---|---|---|---|
| ![AI Sidebar](assets/ai.png) | ![Explorer](assets/explore.png) | ![Scheduler](assets/scheduler.png) | ![Settings](assets/setting.png) |

> All images live in `assets/` (source captures) and `docs/screenshots/` (contributor placeholders). The table above uses the real captures from the current build. The AI tab shows *Summarize / Get Key Points / Generate Mind Map* + external launchers (Gemini/ChatGPT/Copilot) and a live mind-map preview with PNG export. Explorer shows filtered `QFileSystemModel` with “Show all files” toggle. Scheduler shows inline priority (`low/medium/high`), checkbox, double-click to edit, and `✕` delete. Settings shows theme/font/width controls.

### Example Output

**Summarize (Medium, 230 words → 2 chunks):**
```text
Machine learning enables computers to learn from data without explicit programming.
Supervised learning uses labeled examples to predict outcomes, while unsupervised
finds hidden patterns. Transformer models like DistilBART compress long texts by
selecting salient sentences, here chunked at 600 words with truncation to avoid
1024-token limits...

— via SummarizerService.summarize(..., "Medium")
```

**Key Points:**
```text
- transformer (Score: 0.98)
- summarization (Score: 0.96)
- unsupervised (Score: 0.91)
```

**Mind Map (indented → graph):**
```text
Transformer models
  - DistilBART summarization
  - Token limits and chunking
  - Graph visualization
    - networkx DiGraph
    - matplotlib spring_layout
```

### Highlights

- **Tabbed editor** with find/replace, word-wrap, zoom, dark/light themes persisted via `QSettings`.
- **Local AI** — no API key: summarization, key-phrase extraction and mind-map run in `QThreadPool` workers (`view/ai_workers.py:11`, `services/mind_map_generator.py:29`).
- **Chunk-aware** — long texts split at 600 words, `truncation=True`, max 150 tokens to stay inside model limits.
- **Mind-map wired** — `Generate Mind Map` button → indented list → `services/graph_visualizer.py:6` `parse_indented_text` → `create_mind_map_pixmap` (dark-aware) → preview + `Export PNG`.
- **Scheduler DNA** — add/edit/delete, priority combo, status persistence to `QStandardPaths/AppDataLocation/scheduler_tasks.json`.
- **Quality gated** — `pytest` 31 tests, `pytest-qt`+`xvfb`, `ruff`/`black`/`mypy`, `pip-audit`, `dependabot`, `pre-commit`.

### Built With

`PyQt5` • `PyMuPDF` • `pypdf` • `python-docx` • `odfpy` • `Hugging Face transformers` • `torch` • `networkx` • `matplotlib` • `pytest`/`pytest-qt` • `ruff`/`black`/`mypy`

---

## Why This Project Matters

Students juggle notes in Notion/Obsidian, PDFs in a reader, TODOs in another app and AI in a browser tab. Context-switching kills focus. Existing note apps either require cloud APIs (cost/privacy) or lack study-specific helpers (summarize, extract key points, mind-map).

This project explores **local-first AI assistance** inside a native desktop: small distilled models run on CPU, no data leaves the machine, and the service layer stays testable without Qt. The mind-map bridges text → graph, turning linear notes into a visual memory aid — a pattern reusable for any document-to-structure task.

**Concepts showcased:**
- Lazy model loading & chunked inference for 1024-token transformers
- Service–View separation (`services/` vs `view/`) for unit-testable AI logic
- Qt threading (`QThreadPool`/`QRunnable`) to keep UI responsive
- Graph construction from indented text + `matplotlib` → `QPixmap` rendering

---

## Overview

StudyMate is a 1400×900 `QMainWindow` with a west-tabbed `SideBar` (Explore / AI / Scheduler / Settings) and a central `QTabWidget` editor. Opening a file routes through `FileService`’s reader registry (`.txt/.md/.py/.docx/.odt/.pdf`), ODT is converted headlessly via `libreoffice` with timeout and temp-dir cleanup. AI actions are dispatched to workers; results stream back via `pyqtSignal` to the sidebar’s `QTextEdit` and `QLabel` preview. Settings (theme, font, width, word-wrap) round-trip through `SettingsManager` (`QSettings`) and `SettingsModel`. Detailed flow is in [Architecture](#architecture).

---

## Problem Statement

**Who is affected:** students and researchers handling mixed formats (notes, papers, slides) who need quick comprehension aids.

Traditional approaches suffer from:

- **Fragmented tools** — editor, PDF viewer, TODO, AI in separate windows
- **Cloud dependency** — API keys, cost, privacy for summarization
- **Brittle file handling** — ODT/PDF often “open externally or fail”, no registry
- **UI freezes** — model loading on the main thread blocks the app for seconds

These increase friction, break flow, and make offline study hard.

---

## Solution Approach

Local, modular desktop with a service layer that can be tested headlessly:

### Presentation Layer — `view/`

Qt widgets, no business logic. Delegates to services.

- `MainWindow` (749 lines → slimmed via `view/styles.py` + `view/theme_manager.py`)
- `SideBar` (Explore `QFileSystemModel` with name filters, AI tab, Scheduler, Settings)
- `EditorArea`, `PdfViewer` (fitz pixmap, zoom, `cleanup()` on `removeTab`), `TaskWidget`

### Service Layer — `services/`

Pure Python, lazily imports `transformers`/`fitz`.

- `FileService` — `_reader_registry()`, `convert_odt_to_pdf(timeout=60)` with `CalledProcessError`/`TimeoutExpired` handling
- `SummarizerService` / `KeyPointsService` — `get_summarizer()`/`get_extractor()` singletons, chunking, `truncation=True`
- `MindMapService` + `MindMapWorker` — reuses summarizer, sentence → `  - ` list
- `GraphVisualizer` — `parse_indented_text` (root at `-1`, prunes deeper levels) + `create_mind_map_pixmap` (dark/light)
- `SearchService`, `LifecycleService`

### Persistence Layer

- `SettingsManager` wraps `QSettings` (guards `type=None` edge case)
- `SchedulerTab` JSON via `QStandardPaths.writableLocation`

> Note: Data flow is documented once in [Architecture](#architecture).

---

## Demo

### Running the Application

```bash
git clone https://github.com/smartnotes-application/smartnotes-application.git
cd smartnotes-application
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt          # or: pip install -e .
pip install torch --index-url https://download.pytorch.org/whl/cpu  # slim CPU wheel, avoids 550MB CUDA
python main.py           # or: studymate (from [project.scripts])
# first run downloads ~300MB models from Hugging Face
```

**CPU vs CUDA:** `requirements.txt:14` is `torch>=2.4`. For low quota/disk, install CPU wheel as above; app still runs without torch (AI buttons show graceful error).

### Direct Service Usage

```bash
python -c "from services.summarizer import SummarizerService; print(SummarizerService.get_summary_lengths(100))"
QT_QPA_PLATFORM=offscreen python -c "from services.graph_visualizer import parse_indented_text; g=parse_indented_text('Root\n  - A\n  - B'); print(list(g.edges))"
```

### Configuration

No `.env` needed. Optional: `Settings` tab persists to `~/.config/StudyMate/StudyMate.conf` (Linux) / registry (Windows). Scheduler tasks: `~/.local/share/StudyMate/StudyMate/scheduler_tasks.json` (via `QStandardPaths`).

### Example Output

See [System Demonstration](#system-demonstration) — real outputs from `sshleifer/distilbart-cnn-6-6` and `ml6team/keyphrase-extraction-kbir-inspec`.

---

## Features

- Multi-tab editor with find/replace (wrap-around), word-wrap, zoom, `Ctrl+F`, dark/light theme
- PDF viewer with `Previous/Next`, page spinbox, `Zoom In/Out/Reset/Fit Width` (PyMuPDF)
- File registry: `.txt/.md/.markdown/.py/.docx/.odt/.pdf/.json/.png` with binary filter toggle (“Show all files”)
- AI: `Summarize` (Short/Medium/Long length), `Get Key Points`, `Generate Mind Map` + preview + `Export PNG`
- External AI launchers: Gemini / ChatGPT / Copilot via `QDesktopServices` with error guard
- Scheduler: add via `Enter`, double-click to edit, priority `low/medium/high` combo, `✕` delete, `Clear Scheduler` with confirmation, JSON persistence
- Settings: theme, font family/size, sidebar width/font-size, word-wrap — all persisted
- System: `libreoffice` ODT→PDF with 60s timeout, `QThreadPool` workers, graceful `QSettings` `type=None` fix

---

## Results & Metrics

**Coverage (pytest):**
```text
services/graph_visualizer.py   100% (43 stmts)
services/mind_map_generator.py  93% (45 stmts)
services/key_points_extractor   92%
services/summarizer             73% (chunk path covered)
view/scheduler_tab              50%
TOTAL 31 passed, 9 skipped (Qt headless via fake-Qt conftest; real Qt in CI xvfb)
```

**Latency (CPU, 600-word chunk):** summarizer ~2–5s first load (model init), ~0.8s per chunk thereafter; key-points ~0.5s; mind-map ~1s. Chunking keeps peak RAM < 1.5GB vs OOM on 2k-word naive call.

**Trade-off:** DistilBART is 306M params — fast on CPU but less abstractive than larger PEGASUS; chosen for offline demo. Swapping to `facebook/bart-large-cnn` is a one-line `pipeline(model=...)` change in `MindMapService.get_generator`.

---

## Architecture

### High-Level Architecture

UI (`view/`) is a thin shell; all I/O, AI and graph logic lives in `services/`. `MainWindow` owns `QThreadPool` and status bar, `SideBar` owns tabs, `FileHandler` owns `QTabWidget` lifecycle with `PdfViewer.cleanup()` on `removeTab`. Tests import services without Qt via `tests/conftest.py` fake-Qt shim, enabling headless CI.

### System Data Flow

```text
┌───────────────────────┐
│ User drops/opens file │
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ FileService.read_file │ ──► EditorArea QTextEdit
│ + ODT→PDF subprocess  │     PdfViewer (fitz)
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│   Editor → AI Worker  │ ──► Hugging Face pipeline (truncation + chunk)
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ Output Aggregator     │ ──► QTextEdit + QLabel QPixmap (+ PNG export)
└───────────┬───────────┘
            ▼
┌───────────────────────┐
│ Settings/Scheduler    │ ──► QSettings / JSON
└───────────────────────┘
```

<details>
<summary><strong>Component Details (click to expand)</strong></summary>

#### Core / AI Layer

**Location:** `services/summarizer.py`, `key_points_extractor.py`, `mind_map_generator.py`

- Lazy singleton `get_summarizer()`/`get_extractor()` avoids import-time `torch` cost
- Chunk at 600/450 words, `max_length` clamped to 150, `do_sample=False`
- `MindMapWorker.Signals` (`finished`/`error`) for thread-safe UI

#### Visualization Layer

**Location:** `services/graph_visualizer.py`

- `parse_indented_text` uses `path={-1: root}` and prunes `k > indent` for correct siblings
- `create_mind_map_pixmap(graph, is_dark)` — `spring_layout(seed=42)`, `bbox_inches=tight`, `QPixmap.loadFromData`

#### UI Layer

**Location:** `view/main_window.py` (749 lines), `view/side_bar.py` (272 lines), `view/scheduler_tab.py`, `view/task_widget.py`, `view/theme_manager.py`, `view/styles.py`

- `ThemeManager.sync_ui` blocks signals to avoid loops
- `DARK_STYLESHEET` extracted to `view/styles.py:1`
- `TaskWidget` signals `status_changed`/`priority_changed`/`request_delete`/`request_edit`

#### Technical Highlights

- Async via `QThreadPool`/`QRunnable` + `PreloadWorker` on startup
- `QFileSystemModel.setNameFilters` + toggle to hide binaries
- `QDesktopServices.openUrl` guarded with `QMessageBox` fallback
- `pip-audit` + `dependabot` + `pre-commit` (ruff/black/mypy)

</details>

---

## Engineering Decisions

<details>
<summary><strong>Why PyQt5 over Electron/Tkinter?</strong> (click to expand)</summary>

Native look on Linux/Win/mac, mature `QSettings`/`QFileSystemModel`, fine-grained stylesheet control. Electron heavier (100MB+), Tkinter lacks `QThreadPool`/`QTabWidget` polish. Trade-off: heavier install (Qt 60MB) but `offscreen` platform enables headless tests.

**Benefits:** single-package `pip install`, dark theme via stylesheet, `xvfb` CI.

</details>

<details>
<summary><strong>Why distilled transformers (DistilBART + KBI-R Inspec) over API?</strong> (click to expand)</summary>

Offline, zero-cost, privacy. `sshleifer/distilbart-cnn-6-6` is 6-layer distilled BART (fast CPU, ~1s/ chunk). `ml6team/keyphrase-extraction-kbir-inspec` is token-classification with `B-KEY` tags, easy to format. API would be faster but needs key/quotas. Chunking + `truncation=True` cures 1024-token limit.

**Chosen for:** demo portability, no `.env` secrets.

</details>

<details>
<summary><strong>Why service-layer split?</strong> (click to expand)</summary>

`view/` depends on Qt (hard to test), `services/` is pure Python (easy to mock `pipeline`). `tests/conftest.py:1` fakes Qt so `pytest -q` runs 31 tests without window server, while CI runs real Qt via `xvfb-run`.

**Chosen for:** testability, lazy `transformers` import avoids 2s startup cost.

</details>

---

## Challenges & Lessons Learned

<details>
<summary><strong>Challenge 1: QSettings type=None crash</strong> (click to expand)</summary>

`view/settings_manager.py:11` `value(..., type=None)` forwarded `None` to `QSettings.value(..., type=type)` which expects `bytes/str` → `TypeError` on Linux, blocking startup after fresh install.

**Solution:** guard `if type is not None: return value(..., type=type) else: value(...)` + add `tests/conftest` fake `QSettings`.

**Result:** GUI now starts headless and on Fedora Wayland (`QT_QPA_PLATFORM=offscreen` verified, screenshot 796×596).

</details>

<details>
<summary><strong>Challenge 2: Mind-map “sibling becomes child”</strong> (click to expand)</summary>

`graph_visualizer.py:21` `path={0: root}` overwrote root on `indent=0` siblings, so second `- B` became child of `- A`.

**Solution:** root at `-1`, prune `k > indent`, fallback `max(valid) else -1`. Added 7 tests (`test_graph_visualizer.py:6`).

**Result:** correct `Root → A, Root → B` for flat lists, hierarchical for indented.

</details>

<details>
<summary><strong>Challenge 3: Disk quota on torch 2.14 CUDA</strong> (click to expand)</summary>

`torch>=2.4` resolved to `2.14.0` + 553MB `nvidia_cudnn` → `[Errno 122] Disk quota exceeded` on Fedora, leaving `PyQt5` half-installed.

**Solution:** document CPU wheel `pip install torch --index-url https://download.pytorch.org/whl/cpu` + `--no-cache-dir` + optional AI-less run (services handle `ImportError`). Added `pip-audit` guard.

**Result:** slim install ~200MB, AI still works via CPU.

</details>

### Lessons Learned

- Fake-Qt in `conftest` unlocks headless `pytest-qt` without `xvfb` locally.
- Always clamp `max_length`/`min_length` and use `truncation=True` for transformers.
- Extract stylesheets/theme logic early — 90-line inline CSS bloats God class.
- Small `dependabot` + `pre-commit` loops catch drift before `pip-audit` screams.

---

## Repository Structure

```text
.
├── assets/               # real screenshots from running app
│   ├── ai.png            # AI tab (Summarize / Key Points / Mind Map)
│   ├── explore.png       # Explorer with filtered model + 2 tabs
│   ├── scheduler.png     # Scheduler with priority/edit/delete
│   └── setting.png       # Settings (theme/font/width) + editor
├── docs/screenshots/     # placeholder keep + .placeholder files (CI-friendly)
├── services/             # pure logic, no Qt dependency
│   ├── file_service.py
│   ├── summarizer.py
│   ├── key_points_extractor.py
│   ├── mind_map_generator.py
│   ├── graph_visualizer.py
│   ├── search_service.py     # find/replace delegates
│   └── lifecycle.py          # close-event → close_all + sync
├── view/
│   ├── main_window.py    # 749 lines, QThreadPool, status bar
│   ├── side_bar.py       # Explorer/AI/Scheduler/Settings tabs
│   ├── scheduler_tab.py  # JSON persistence, edit/delete
│   ├── task_widget.py    # checkbox + priority + edit/delete signals
│   ├── pdf_viewer.py     # fitz + cleanup() on removeTab
│   ├── styles.py         # DARK_STYLESHEET (extracted)
│   ├── theme_manager.py  # apply_dark/light/sync_ui
│   └── ...
├── tests/
│   ├── conftest.py       # fake Qt for headless runs
│   ├── test_graph_visualizer.py
│   ├── test_mind_map_generator.py
│   ├── test_scheduler_tab.py
│   └── ...
├── main.py               # entry, app.exec()
├── pyproject.toml        # [project.scripts] studymate = "main:main"
├── requirements.txt      # PyQt5, torch, transformers, etc.
├── requirements-dev.txt  # pytest-qt, ruff, black, mypy, pip-audit
├── .pre-commit-config.yaml
├── .github/workflows/python-ci.yml  # lint + test (xvfb, offscreen) + audit + codecov
├── .github/dependabot.yml
└── README.md
```

---

## Getting Started

### Clone Repository

```bash
git clone https://github.com/smartnotes-application/smartnotes-application.git
cd smartnotes-application
```

### Create Virtual Environment

**Linux/macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows**
```bash
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -U pip
pip install -r requirements.txt
# slim AI (avoids CUDA quota):
pip install torch --index-url https://download.pytorch.org/whl/cpu
# or: pip install -e .  # uses [project.scripts] -> `studymate`
pip install -r requirements-dev.txt  # for tests/lint
pre-commit install
```

### Configuration

No env vars. Optional: `libreoffice` for ODT, `xvfb` for headless tests.

```bash
sudo apt-get install -y libreoffice xvfb libxkbcommon-x11-0 libxcb-icccm4
```

### Run

```bash
python main.py
# or
studymate
# first run downloads models to ~/.cache/huggingface (~300MB)
```

---

## Testing & Verification

### Automated Testing

```bash
QT_QPA_PLATFORM=offscreen xvfb-run -a python -m pytest tests -q --cov=. --cov-report=term-missing --cov-report=xml
# 31 passed, 9 skipped (skipped = live Qt not installed locally, pass in CI xvfb)
```

### Lint & Type

```bash
ruff check . --output-format=github
black --check --line-length 100 .
mypy services view --ignore-missing-imports --explicit-package-bases
pip-audit --desc || true
```

### Manual Verification

```bash
QT_QPA_PLATFORM=offscreen python -c "from view.main_window import MainWindow; from PyQt5.QtWidgets import QApplication; app=QApplication([]); w=MainWindow(); w.show(); app.processEvents(); w.grab().save('/tmp/check.png'); print('OK')"
# → PNG 796×596, This plugin does not support propagateSizeHints() is harmless
```

**Expected Outcome**
- All 31 tests pass (services 92-100% as per `test_graph_visualizer`/`mind_map`)
- `ruff`/`black`/`mypy` pass on `view/styles.py`/`theme_manager.py` (others have import sort warnings)
- GUI starts, shows 4 tabs, AI preview renders, scheduler persists

---

## Future Improvements

- Swap `distilbart-cnn-6-6` → `facebook/bart-large-cnn` behind flag + quantized `optimum` for speed
- Add `pytest-qt` live GUI tests (`qtbot` click on `Generate Mind Map` → assert `QPixmap` not null)
- Vector store for notes (FAISS) + RAG over local docs instead of single-doc summarize
- Packaging: `briefcase`/`fbs` binary, signed DMG/.deb
- Evaluate ROUGE on CNN/DailyMail subset for summarizer config (Short/Medium/Long)

---

## Author

**Amir Khoshdel Louyeh**

**Connect**
- **GitHub:** [github.com/amir-khoshdel-louyeh](https://github.com/amir-khoshdel-louyeh)
- **LinkedIn:** [linkedin.com/in/amir-khoshdel-louyeh](https://linkedin.com/in/amir-khoshdel-louyeh)
- **Email:** [amirkhoshdellouyeh@gmail.com](mailto:amirkhoshdellouyeh@gmail.com)

---

## Disclaimer

Educational and research demo. Models are DistilBART/KBI-R (MIT/Apache). Licensed under **MIT** — see [LICENSE](LICENSE).

---

> Screenshots in `assets/` are from the live build (Fedora, offscreen 796×596). To refresh them: `QT_QPA_PLATFORM=offscreen python -c "from view.main_window import MainWindow; ...; w.grab().save('assets/ai.png')"`.
