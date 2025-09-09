from typing import Optional
import os

def synthesize_speech(text: str, out_path: str, lang: str = 'en') -> bool:
    """
    Default: gTTS (requires internet). Saves MP3. Returns True/False.
    Swap engine as needed.
    """
    if not text or not text.strip():
        print("TTS Error: No text provided")
        return False
    
    try:
        from gtts import gTTS
        
        # Map some common language codes to gTTS supported codes
        lang_mapping = {
            'hi': 'hi',      # Hindi
            'es': 'es',      # Spanish
            'fr': 'fr',      # French
            'de': 'de',      # German
            'it': 'it',      # Italian
            'pt': 'pt',      # Portuguese
            'ru': 'ru',      # Russian
            'ja': 'ja',      # Japanese
            'ko': 'ko',      # Korean
            'zh': 'zh',      # Chinese
            'ar': 'ar',      # Arabic
            'en': 'en'       # English
        }
        
        # Use mapped language or default to English
        tts_lang = lang_mapping.get(lang, 'en')
        print(f"TTS: Using language '{tts_lang}' for input '{lang}'")
        
        tts = gTTS(text=text, lang=tts_lang)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        tts.save(out_path)
        
        # Verify file was created
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"TTS: Audio file created successfully at {out_path}")
            return True
        else:
            print(f"TTS: Audio file creation failed or file is empty")
            return False
            
    except Exception as e:
        print(f"TTS Error: {e}")
        import traceback
        traceback.print_exc()
        return False
