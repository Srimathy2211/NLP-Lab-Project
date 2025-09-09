from typing import Optional, List
import re

def _split_text_into_chunks(text: str, max_chars: int = 3800) -> List[str]:
    """
    Split text into chunks not exceeding max_chars, preferably on sentence boundaries.
    """
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    for s in sentences:
        s_len = len(s)
        if current_len + s_len + (1 if current else 0) <= max_chars:
            current.append(s)
            current_len += s_len + (1 if current else 0)
        else:
            if current:
                chunks.append(' '.join(current).strip())
            # If a single sentence is too large, hard-split it
            if s_len > max_chars:
                start = 0
                while start < s_len:
                    end = min(start + max_chars, s_len)
                    chunks.append(s[start:end])
                    start = end
                current = []
                current_len = 0
            else:
                current = [s]
                current_len = s_len
    if current:
        chunks.append(' '.join(current).strip())
    return chunks


def maybe_translate(text: str, target_lang: str, source_lang: Optional[str] = None) -> Optional[str]:
    """
    Try to translate `text` to `target_lang` using deep-translator.
    Returns translated text, or None on failure.
    """
    if not text or not text.strip():
        print("ERROR: Empty or None text provided")
        return None
        
    try:
        from deep_translator import GoogleTranslator, MyMemoryTranslator
        try:
            # LibreTranslate is optional; not all versions include it
            from deep_translator import LibreTranslateTranslator  # type: ignore
            has_libre = True
        except Exception:
            LibreTranslateTranslator = None  # type: ignore
            has_libre = False

        print(f"Translating to {target_lang} using Google Translate")
        print(f"Input text length: {len(text)}")

        # Sanitize input (remove control chars that can confuse providers)
        text = re.sub(r"[\u200B-\u200F\u202A-\u202E]", "", text)
        text = text.replace("\r", "")
        
        # Prepare chunked text to stay under provider limits (~5000). Start ~1800 to be safer for Indic scripts.
        chunks = _split_text_into_chunks(text, max_chars=1800)
        print(f"Translating in {len(chunks)} chunk(s)")

        # Prefer provider auto-detection first; detected source only as secondary hint
        src = 'auto'
        detected_src = (source_lang or '').strip().lower()

        # First attempt: Google Translate (chunked)
        google_results: List[str] = []
        try:
            g_translator = GoogleTranslator(source=src, target=target_lang)
            for idx, chunk in enumerate(chunks):
                last_err = None
                for attempt in range(2):
                    try:
                        translated = g_translator.translate(chunk)
                        print(f"Google chunk {idx+1}/{len(chunks)} try {attempt+1}: {translated[:80] if translated else 'None'}...")
                        if translated:
                            google_results.append(translated)
                            break
                    except Exception as e:
                        last_err = e
                else:
                    raise ValueError(f"Google failed for chunk {idx+1}: {last_err}")
            combined = '\n'.join(google_results)
            if combined.strip() and (src == target_lang or combined.strip() != text.strip()):
                print("Google translation successful (combined)")
                return combined
            print("Google returned empty/unchanged after combining; will try fallback")
        except Exception as ge:
            print(f"GoogleTranslator error: {ge}; will try fallback")

        # Fallback attempt: MyMemory (chunked)
        try:
            print("Trying fallback: MyMemoryTranslator")
            mm_results: List[str] = []
            mm = MyMemoryTranslator(source=src, target=target_lang)
            for idx, chunk in enumerate(chunks):
                last_err = None
                for attempt in range(2):
                    try:
                        translated_mm = mm.translate(chunk)
                        print(f"MyMemory chunk {idx+1}/{len(chunks)} try {attempt+1}: {translated_mm[:80] if translated_mm else 'None'}...")
                        if translated_mm:
                            mm_results.append(translated_mm)
                            break
                    except Exception as e:
                        last_err = e
                else:
                    raise ValueError(f"MyMemory failed for chunk {idx+1}: {last_err}")
            combined_mm = '\n'.join(mm_results)
            if combined_mm.strip() and (src == target_lang or combined_mm.strip() != text.strip()):
                print("MyMemory translation successful (combined)")
                return combined_mm
        except Exception as me:
            print(f"MyMemoryTranslator error: {me}")

        # Fallback attempt: LibreTranslate (if available)
        if has_libre and LibreTranslateTranslator is not None:
            try:
                print("Trying fallback: LibreTranslateTranslator")
                lt_results: List[str] = []
                # Use a public endpoint; for production, host your own
                lt = LibreTranslateTranslator(source=src, target=target_lang, 
                                              api_url="https://libretranslate.de/translate")
                for idx, chunk in enumerate(chunks):
                    last_err = None
                    for attempt in range(2):
                        try:
                            translated_lt = lt.translate(chunk)
                            print(f"LibreTranslate chunk {idx+1}/{len(chunks)} try {attempt+1}: {translated_lt[:80] if translated_lt else 'None'}...")
                            if translated_lt:
                                lt_results.append(translated_lt)
                                break
                        except Exception as e:
                            last_err = e
                    else:
                        raise ValueError(f"LibreTranslate failed for chunk {idx+1}: {last_err}")
                combined_lt = '\n'.join(lt_results)
                if combined_lt.strip() and (src == target_lang or combined_lt.strip() != text.strip()):
                    print("LibreTranslate translation successful (combined)")
                    return combined_lt
            except Exception as le:
                print(f"LibreTranslateTranslator error: {le}")

        # Second pass with smaller chunks if all failed
        small_chunks = _split_text_into_chunks(text, max_chars=800)
        if len(small_chunks) > len(chunks):
            print(f"Retrying with smaller chunks: {len(small_chunks)}")
            for provider in ('google', 'mymemory', 'libre'):
                results: List[str] = []
                try:
                    if provider == 'google':
                        g = GoogleTranslator(source=src, target=target_lang)
                        for idx, ch in enumerate(small_chunks):
                            results.append(g.translate(ch) or '')
                    elif provider == 'mymemory':
                        m = MyMemoryTranslator(source=src, target=target_lang)
                        for idx, ch in enumerate(small_chunks):
                            results.append(m.translate(ch) or '')
                    elif provider == 'libre' and has_libre and LibreTranslateTranslator is not None:
                        l = LibreTranslateTranslator(source=src, target=target_lang, api_url="https://libretranslate.de/translate")
                        for idx, ch in enumerate(small_chunks):
                            results.append(l.translate(ch) or '')
                    combined_small = '\n'.join(results).strip()
                    if combined_small and (src == target_lang or combined_small != text.strip()):
                        print(f"Second-pass {provider} successful")
                        return combined_small
                except Exception as e:
                    print(f"Second-pass {provider} error: {e}")

        # Pivot fallback: source -> en -> target (helps when direct pair fails)
        try:
            if target_lang != 'en':
                print("Trying pivot translation via English")
                # First hop to English
                g1 = GoogleTranslator(source=src, target='en')
                to_en_chunks: List[str] = []
                for ch in chunks:
                    to_en_chunks.append(g1.translate(ch) or ch)
                mid_text = '\n'.join(to_en_chunks)
                # Second hop English to target
                g2 = GoogleTranslator(source='en', target=target_lang)
                final_chunks: List[str] = []
                for ch in _split_text_into_chunks(mid_text, max_chars=1800):
                    final_chunks.append(g2.translate(ch) or ch)
                pivot_result = '\n'.join(final_chunks).strip()
                if pivot_result and pivot_result != text.strip():
                    print("Pivot translation successful")
                    return pivot_result
        except Exception as pe:
            print(f"Pivot translation error: {pe}")

        # Final attempt using detected source explicitly if available
        if detected_src and detected_src != 'auto':
            try:
                print(f"Final attempt with detected source: {detected_src}")
                g = GoogleTranslator(source=detected_src, target=target_lang)
                res = []
                for ch in chunks:
                    res.append(g.translate(ch) or '')
                final = '\n'.join(res).strip()
                if final and final != text.strip():
                    print("Final attempt successful")
                    return final
            except Exception as fe:
                print(f"Final attempt error: {fe}")

        print("All translators failed or returned empty/unchanged text")
        return None

    except Exception as e:
        print(f"Translator module error: {e}")
        import traceback
        traceback.print_exc()
        return None
