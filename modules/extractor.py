import os
from pathlib import Path
from io import BytesIO
from PIL import Image

def _extract_text_pdf(path):
    # First try text-based PDF extraction; if it fails, fallback to OCR via modules.ocr
    try:
        from pdfminer.high_level import extract_text as pdf_extract_text
        text = pdf_extract_text(path) or ""
        # Heuristic: if too little text, treat as scanned and OCR
        if len(text.strip()) < 20:
            from .ocr import ocr_image_or_pdf
            return ocr_image_or_pdf(path)
        return text
    except Exception:
        from .ocr import ocr_image_or_pdf
        return ocr_image_or_pdf(path)

def _extract_text_docx(path):
    try:
        import docx
        doc = docx.Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
        if len(text.strip()) >= 20:
            return text
        # Fallback: scanned DOCX with images only → OCR embedded images
        try:
            from .ocr import ocr_image_or_pdf
            ocr_chunks = []
            # Explore related parts for images
            for rel in doc.part.related_parts.values():
                try:
                    if hasattr(rel, 'content_type') and str(rel.content_type).startswith('image/'):
                        blob = rel.blob  # bytes
                        img = Image.open(BytesIO(blob))
                        # Save to a temporary in-memory file is fine; ocr function expects a path, so we convert via temp file
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tf:
                            img.save(tf.name, format='PNG')
                            tf.flush()
                            ocr_text = ocr_image_or_pdf(tf.name)
                            if ocr_text and ocr_text.strip():
                                ocr_chunks.append(ocr_text)
                except Exception:
                    continue
            if ocr_chunks:
                return "\n".join(ocr_chunks)
        except Exception:
            pass
        return text
    except Exception:
        return ""

def _extract_text_txt(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

def _extract_text_image(path):
    from .ocr import ocr_image_or_pdf
    return ocr_image_or_pdf(path)

def extract_text_from_file(path):
    ext = Path(path).suffix.lower()
    if ext == '.pdf':
        return _extract_text_pdf(path)
    elif ext == '.docx':
        return _extract_text_docx(path)
    elif ext == '.txt':
        return _extract_text_txt(path)
    elif ext in ['.png', '.jpg', '.jpeg', '.tiff']:
        return _extract_text_image(path)
    else:
        return ""
