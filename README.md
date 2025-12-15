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

- Python 3.9+
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

## Screenshots (Placeholders)

Add images under `docs/screenshots/` and update the paths below.

```text
docs/
	screenshots/
		main-window.png
		sidebar-ai.png
		pdf-viewer.png
		scheduler.png
```

![Main Window](docs/screenshots/main-window.png)

![AI Sidebar](docs/screenshots/sidebar-ai.png)

![PDF Viewer](docs/screenshots/pdf-viewer.png)

![Scheduler](docs/screenshots/scheduler.png)

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

Recommended next improvements:
- Chunk long texts for summarization (token-limit aware)
- Persist scheduler tasks to disk
- Wire mind-map visualizer into the UI and add export
- Add tests (e.g., `pytest`, `pytest-qt`) and CI

## License

Add your license of choice here (e.g., MIT). If you already have a license file, link it.

