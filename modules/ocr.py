from PIL import Image, ImageOps, ImageFilter
import pytesseract
import tempfile
import os
import re

def _preprocess_image(img: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(img)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    w, h = gray.size
    if min(w, h) < 1000:
        scale = 2
        gray = gray.resize((w * scale, h * scale), Image.LANCZOS)
    gray = ImageOps.autocontrast(gray)
    return gray

_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")
_TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")
_LATIN_RANGE = re.compile(r"[A-Za-z]")


def _guess_script(text: str) -> str:
    if _DEVANAGARI_RANGE.search(text):
        return 'hin'
    if _TAMIL_RANGE.search(text):
        return 'tam'
    return 'eng'


def _char_stats(text: str) -> dict:
    total = len(text) or 1
    latin = len(_LATIN_RANGE.findall(text))
    dev = len(_DEVANAGARI_RANGE.findall(text))
    tam = len(_TAMIL_RANGE.findall(text))
    digits = sum(ch.isdigit() for ch in text)
    spaces = text.count(' ')
    punct = sum(ch in ',.;:/\\-_' for ch in text)
    printable = sum(ch.isprintable() for ch in text)
    return {
        'latin_ratio': latin / total,
        'dev_ratio': dev / total,
        'tam_ratio': tam / total,
        'digit_ratio': digits / total,
        'space_ratio': spaces / total,
        'punct_ratio': punct / total,
        'printable_ratio': printable / total,
        'len': len(text),
    }


def _score_text_for_lang(text: str, lang: str) -> float:
    t = text.strip()
    if not t:
        return 0.0
    s = _char_stats(t)
    # Script match target
    target_script = 0.0
    if 'hin' in lang:
        target_script = s['dev_ratio']
    elif 'tam' in lang:
        target_script = s['tam_ratio']
    else:  # eng, spa and others latin-based
        target_script = s['latin_ratio']
    # Quality heuristics
    alnum_like = s['latin_ratio'] + s['dev_ratio'] + s['tam_ratio'] + s['digit_ratio']
    noise_penalty = max(0.0, 1.0 - s['printable_ratio'])
    length_bonus = min(1.0, s['len'] / 200.0)  # cap bonus
    return (2.5 * target_script) + (0.8 * alnum_like) + (0.5 * length_bonus) - (1.0 * noise_penalty)


def _ocr_with_langs(img: Image.Image, langs: list[str]) -> str:
    best_text = ""
    best_score = float('-inf')
    for lang in langs:
        try:
            txt = pytesseract.image_to_string(img, lang=lang, config='--oem 3 --psm 6') or ""
            ltxt = txt.strip()
            score = _score_text_for_lang(ltxt, lang)
            if score > best_score:
                best_text = ltxt
                best_score = score
        except Exception:
            continue
    return best_text


def _latin_ratio(text: str) -> float:
    if not text:
        return 0.0
    latin_chars = sum(1 for c in text if ('A' <= c <= 'Z') or ('a' <= c <= 'z') or ('0' <= c <= '9') or c in ' ,.;:/\\-_()[]{}"\'\n')
    return latin_chars / max(1, len(text))


def ocr_image_or_pdf(path):
    ext = os.path.splitext(path)[1].lower()
    # Candidates cover multiple scripts and combinations without prioritizing a single language
    base_candidates = ['eng', 'hin', 'tam', 'spa', 'eng+hin', 'eng+tam', 'eng+spa']

    if ext in ['.png', '.jpg', '.jpeg', '.tiff']:
        img = Image.open(path)
        img = _preprocess_image(img)
        # Try broad candidates and select best by script-aware scoring
        first_pass = _ocr_with_langs(img, base_candidates)
        # Refine based on detected script in first pass
        guessed = _guess_script(first_pass)
        refine = [guessed, f'eng+{guessed}'] if guessed != 'eng' else ['eng']
        refined = _ocr_with_langs(img, refine)
        # Choose the better by scoring using appropriate lang guess
        score_first = _score_text_for_lang(first_pass, guessed if guessed != 'eng' else 'eng')
        score_ref = _score_text_for_lang(refined, guessed if guessed != 'eng' else 'eng')
        return refined if score_ref >= score_first else first_pass

    try:
        import shutil, subprocess
        if shutil.which('pdftoppm'):
            with tempfile.TemporaryDirectory() as td:
                out_prefix = os.path.join(td, 'page')
                subprocess.run(['pdftoppm', '-r', '300', path, out_prefix, '-png'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                text_chunks = []
                for fname in sorted(os.listdir(td)):
                    if fname.endswith('.png'):
                        fp = os.path.join(td, fname)
                        img = Image.open(fp)
                        img = _preprocess_image(img)
                        first_pass = _ocr_with_langs(img, base_candidates)
                        guessed = _guess_script(first_pass)
                        refine = [guessed, f'eng+{guessed}'] if guessed != 'eng' else ['eng']
                        refined = _ocr_with_langs(img, refine)
                        text_chunks.append(refined if len(refined) > len(first_pass) else first_pass)
                return "\n".join(filter(None, text_chunks))
    except Exception:
        pass

    return ""  # Caller handles empty text
