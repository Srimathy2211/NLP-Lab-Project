from typing import Optional

def maybe_summarize(text: str, max_len: int = 150) -> Optional[str]:
    """
    Summarize long text (heuristic: if > 800 chars).
    """
    if len(text) < 800:
        return text
    try:
        from transformers import pipeline
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        out = summarizer(text, max_length=max_len, min_length=max_len//3, do_sample=False)
        if isinstance(out, list) and out:
            return out[0].get("summary_text", None)
    except Exception:
        pass
    return None
