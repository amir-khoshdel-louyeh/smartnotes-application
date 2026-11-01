# StudyMate — SmartNotes Desktop

A local-first study workspace for reading notes and PDFs, summarising them, extracting key points and turning them into mind maps — with no API keys and no document leaving the machine.

![StudyMate AI sidebar](assets/ai.png)

`Python 3.11+` · `PyQt5` · `Hugging Face Transformers` · Desktop application · Working prototype

## At a glance

| | |
|---|---|
| **Problem** | Study material is split across editors, PDF readers, task lists and browser-based AI tools |
| **Approach** | Native PyQt5 workspace with local distilled transformer models and a testable service layer |
| **Formats** | `.txt`, `.md`, `.py`, `.docx`, `.odt`, `.pdf` |
| **AI features** | Summarisation, key-phrase extraction, mind-map generation (DistilBART + KBIR) |
| **Tests** | **45 passed** (`pytest`, headless Qt) |
| **Privacy** | No cloud AI; inference runs on the local CPU |
| **Role** | Solo — architecture, UI, services, tests, packaging |

## Overview

StudyMate combines a tabbed editor, PDF viewer, file explorer, scheduler and AI sidebar in one desktop window. Its distinguishing choice is local inference: a distilled BART summariser and a KBIR key-phrase model are loaded lazily and run through a `QThreadPool`, so the interface stays responsive while a model is working and no note text is sent to a third party.

The codebase separates Qt views (`view/`) from pure-Python services (`services/`). That boundary is what makes the AI and graph logic testable without a display, and it keeps model-specific details out of the widgets.

## Screenshots

| AI sidebar | Editor & explorer |
|---|---|
| ![](assets/ai.png) | ![](assets/explore.png) |

| Scheduler | Settings |
|---|---|
| ![](assets/scheduler.png) | ![](assets/setting.png) |

The AI panel offers three summary lengths, key-point extraction, mind-map generation and explicit external-AI links (Gemini / ChatGPT / Copilot) for users who prefer them. The scheduler stores tasks as JSON under `QStandardPaths`; settings (theme, font, sidebar width, word wrap) round-trip through `QSettings`.

## Architecture

```text
view/ (Qt widgets only)
  MainWindow · SideBar · EditorArea · PdfViewer · TaskWidget
        │
        ▼
services/ (pure Python, lazily imports transformers/fitz)
  FileService      reader registry, ODT→PDF via LibreOffice
  SummarizerService  distilbart-cnn-6-6, 600-word chunks
  KeyPointsService   kbir-inspec, B-KEY filtering
  MindMapService     summary → indented outline
  GraphVisualizer    networkx layout → matplotlib → QPixmap
  SearchService · LifecycleService
        │
        ▼
Persistence: QSettings · scheduler JSON · exported PDF/PNG
```

AI work is dispatched through `QRunnable` workers and returns via Qt signals. Models are singleton-loaded on first use, which keeps application start-up fast and avoids importing `torch` until an AI action is requested.

## Testing

```bash
python -m pytest tests -q
```

Current result: **45 passed**. The suite covers file-service readers, search, scheduler behaviour, settings, lifecycle handling, graph parsing and mind-map generation, plus `pytest-qt` widget tests for the main window and scheduler tab. Model inference itself is mocked or bypassed in unit tests — the tests verify orchestration, not summarisation quality.

```bash
ruff check .        # lint
black --check .     # formatting
mypy services       # types (where configured)
```

## Getting started

```bash
git clone https://github.com/amir-khoshdel-louyeh/smartnotes-application.git
cd smartnotes-application
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# CPU-only PyTorch avoids the large CUDA wheel:
pip install torch --index-url https://download.pytorch.org/whl/cpu
python main.py
```

The first AI action downloads roughly 300 MB of model weights from Hugging Face and caches them locally. Without `torch`/`transformers`, the editor still works; AI actions surface a graceful error instead of crashing.

`.odt` support additionally requires LibreOffice on `PATH`.

## Engineering notes

- **Lazy singleton models.** Importing `transformers` and loading weights inside the worker keeps start-up cheap and makes the failure mode explicit.
- **Chunking for a 1024-token encoder.** Long notes are split at 600 words with truncation, instead of silently truncating the whole document.
- **Dark-aware mind maps.** Graph colours are chosen from the active theme before rendering to a `QPixmap`, so exported images remain legible.
- **Service/view split.** The highest-value structural decision: AI orchestration and graph construction can be unit-tested headlessly.

## Limitations

- Summarisation quality is bounded by small distilled models; no ROUGE or human evaluation is reported, so the README makes no quality claim.
- CPU inference is slow on long documents (seconds per chunk); there is no GPU path or streaming output.
- No cloud sync, multi-device support, or collaborative editing.
- `.odt` conversion depends on an external LibreOffice binary and is not covered end-to-end in tests.
- Screenshots show the light theme at 1920×1080; high-DPI and Wayland fractional scaling were not systematically evaluated.
- Packaging is source-based; no signed installer is produced.

## Roadmap

- Streaming token output for summaries.
- Retrieval over a notes folder (local embeddings) rather than one document at a time.
- Export a study pack (summary + key points + mind map) as a single PDF.
- Benchmark summary quality against a small labelled set.

## Repository structure

```text
smartnotes-application/
├── main.py                  # Application bootstrap
├── view/                    # Qt widgets, workers, theme, icons
├── services/                # File, AI, search, graph, lifecycle logic
├── tests/                   # 45 pytest / pytest-qt tests
├── assets/                  # Screenshots used here
├── docs/                    # Contributor notes
├── requirements.txt · pyproject.toml
└── .pre-commit-config.yaml
```

## Tech stack

`Python` · `PyQt5` · `transformers` / `torch` · `PyMuPDF` · `python-docx` / `odfpy` · `networkx` / `matplotlib` · `pytest` / `pytest-qt` · `ruff` / `black` / `mypy`

## Author

**Amir Khoshdel Louyeh**
[GitHub](https://github.com/amir-khoshdel-louyeh) · [LinkedIn](https://www.linkedin.com/in/amir-khoshdel-louyeh)
