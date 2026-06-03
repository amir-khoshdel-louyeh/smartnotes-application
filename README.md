# StudyMate (SmartNotes Application)

A lightweight study notes application built with PyQt5. Create and edit notes, view PDFs, extract summaries and key points with Hugging Face transformers, and manage daily tasks via a simple scheduler.

## Features

- Text editor with multi-tab support and find/replace
- Light/Dark themes, adjustable fonts and word wrap
- PDF viewer (rendered via PyMuPDF) with zoom and page navigation
- Open `.txt`, `.md`, `.py`, `.docx`, `.odt` (ODT converts to PDF)
- AI utilities:
	- Summarization (configurable length)
	- Key points extraction (local model; placeholder for online API)
- Simple daily scheduler (add tasks, mark done)

## Requirements

- Python 3.11+ (tested on 3.11–3.14)
- Linux/macOS/Windows (Linux tested)
- System dependencies:
	- `libreoffice` (for `.odt` → `.pdf` conversion)

On Debian/Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y libreoffice
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

First run downloads ML models (hundreds of MB). This may take a few minutes depending on your connection.

## Screenshots

> Screenshots are stored under `docs/screenshots/` – run the app and capture them, or contribute your own. Placeholders below will render once images exist.

| Main Window | AI Sidebar | PDF Viewer | Scheduler |
|---|---|---|---|
| `docs/screenshots/main-window.png` | `docs/screenshots/sidebar-ai.png` | `docs/screenshots/pdf-viewer.png` | `docs/screenshots/scheduler.png` |

## Tips & Notes

- Summarizer and key-points models are loaded lazily on first use.
- For better performance with Torch, a CUDA-capable GPU is optional but not required.
- Requirements include `matplotlib` and `networkx` for mind-map graph visuals used by the visualizer service.

## Troubleshooting

- Qt platform plugin errors (Linux):
	- Ensure required X11/Wayland packages are installed (e.g., `libxcb` family). Try running from a terminal to see the exact missing library.
- ODT to PDF conversion fails:
	- Verify `libreoffice` is installed and in your `PATH`.
- First-run model download errors:
	- Check internet connectivity and retry; you can pre-download models via `transformers` cache if needed.

## Development

- Code entrypoint: `main.py`
- UI components: `view/`
- Services (AI/graphs): `services/`
- Quick setup for contributors:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Recent improvements:
- Dependencies updated to support Python 3.11–3.14 and secure versions
- Chunk-aware summarization, persisted scheduler, wired mind-map visualizer
- Tests with `pytest` and CI on 3.11–3.14

## License

MIT – see [LICENSE](LICENSE).

