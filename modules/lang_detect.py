def detect_language(text: str):
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return ""
