# Document-to-Speech Assistant for the Illiterate

A Flask-based app that converts uploaded documents (PDF, DOCX, TXT, images/scanned PDFs) into natural-sounding audio in a chosen language, with optional translation and summarization.

## Features
- Upload PDF/DOCX/TXT/Images
- Extract text via pdfminer.six/python-docx or OCR (pytesseract)
- Language detection (langdetect)
- Optional translation (Hugging Face MarianMT or M2M100)
- Optional summarization (T5/BART) for long docs
- Text-to-Speech with gTTS (default) or pyttsx3/Coqui/Azure/Google Cloud (extensible)
- Simple web UI (Upload → Listen/Download)

## Quickstart
1. **Install system dependencies (Linux/Mac)**  
   - Tesseract OCR:
     - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
     - Mac (Homebrew): `brew install tesseract`
   - (Windows) Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

2. **Create & activate a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

> Note: `transformers`, `torch`, and `sentencepiece` are needed if you enable translation/summarization. You may comment them out in `requirements.txt` if you prefer minimal install.

4. **Run the app**
```bash
export FLASK_APP=app.py
flask run  # or: python app.py
```
Open http://127.0.0.1:5000

## Configuration
- Default TTS is **gTTS** (needs internet). To switch to offline/other providers, edit `modules/tts.py`.
- Translation/summarization are optional and lazy-loaded. If models aren't available, the app will gracefully skip those steps.
- Upload size limits and allowed types can be tweaked in `app.py`.

## Project Structure
```
document-to-speech/
│── app.py
│── requirements.txt
│── README.md
│
├── static/
│   ├── css/
│   ├── js/
│   └── audio/            # generated audio files
├── templates/
│   └── index.html        # Upload & playback UI
├── uploads/              # user uploads
├── modules/
│   ├── extractor.py
│   ├── ocr.py
│   ├── lang_detect.py
│   ├── translator.py
│   ├── summarizer.py
│   ├── tts.py
│   └── utils.py
├── tests/
├── docs/
└── models/
```

## Notes
- For rural/offline scenarios, consider `pyttsx3` or Coqui TTS and deploy on a local server/device.
- For advanced voices (neural), wire up Azure/Google Cloud TTS in `modules/tts.py`.

## License
MIT
