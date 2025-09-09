import os
import uuid
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash, jsonify, session
from modules.extractor import extract_text_from_file
from modules.lang_detect import detect_language
from modules.translator import maybe_translate
from modules.summarizer import maybe_summarize
from modules.tts import synthesize_speech
from modules.utils import allowed_file, secure_filename_safe

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET", "devkey")
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['AUDIO_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'audio')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'tiff'}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            # Start with a clean session for a new upload to avoid stale data
            session.clear()
            # Use a unique filename per upload to avoid collisions/caching
            unique_prefix = str(uuid.uuid4())[:8]
            filename = f"{unique_prefix}_" + secure_filename_safe(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # pipeline controls
            want_summary = request.form.get('want_summary') == 'on'

            # 1) Extract text
            text = extract_text_from_file(save_path)

            if not text or not text.strip():
                flash('Could not extract any text. Try a clearer scan or another file.', 'error')
                return redirect(request.url)

            # 2) Detect language
            src_lang = detect_language(text)

            # 3) Optional summarization
            text_for_display = text
            if want_summary:
                text_for_display = maybe_summarize(text) or text  # fallback to original

            # 4) Store in session and show result
            session['original_text'] = text_for_display
            session['src_lang'] = src_lang
            session['chars'] = len(text_for_display)
            # Reset any prior translation/audio state for a fresh upload
            session['translated_text'] = None
            session['target_lang'] = None
            session['audio_url'] = None
            
            return render_template('index.html', 
                                   original_text=text_for_display,
                                   src_lang=src_lang,
                                   chars=len(text_for_display),
                                   translated_text=None,
                                   target_lang=None)

        else:
            flash('File type not allowed.', 'error')
            return redirect(request.url)

    # GET request - show stored data from session
    return render_template('index.html',
                           original_text=session.get('original_text'),
                           src_lang=session.get('src_lang'),
                           chars=session.get('chars'),
                           translated_text=session.get('translated_text'),
                           target_lang=session.get('target_lang'),
                           audio_url=session.get('audio_url'))

@app.after_request
def add_no_cache_headers(response):
    """Prevent browsers/proxies from caching dynamic pages to avoid stale content."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/translate', methods=['POST'])
def translate():
    """Handle translation requests"""
    try:
        data = request.get_json(silent=True) or {}
        text = data.get('text')
        target_lang = (data.get('target_lang', '') or '').strip().lower()
        
        if not target_lang:
            return jsonify({'success': False, 'error': 'Missing target language'})
        # Basic validation for language code
        if len(target_lang) not in (2, 3, 5):
            return jsonify({'success': False, 'error': f'Invalid target language code: {target_lang}. Use ISO code like en, hi, ta.'})
        
        # If text not provided by client, use the original text from session
        if not text:
            text = session.get('original_text', '')
        
        # Debug logging to trace stale content issues
        try:
            print("=== Translate Debug ===")
            print(f"Target lang: {target_lang}")
            incoming_preview = (text or '')[:120].replace('\n', ' ')
            session_preview = (session.get('original_text', '') or '')[:120].replace('\n', ' ')
            print(f"Incoming text[0:120]: {incoming_preview}")
            print(f"Session original_text[0:120]: {session_preview}")
        except Exception:
            pass

        if not text:
            return jsonify({'success': False, 'error': 'No text available to translate'})
        if len(text) > 12000:
            return jsonify({'success': False, 'error': f'Text too long to translate ({len(text)} chars). Try summarizing first.'})
        
        # Perform translation, pass along detected src language if available
        translated_text = maybe_translate(text, target_lang, session.get('src_lang'))
        
        if translated_text:
            # Store the translated text in session
            session['translated_text'] = translated_text
            session['target_lang'] = target_lang
            return jsonify({'success': True, 'translated_text': translated_text})
        else:
            preview = (text or '')[:80].replace('\n', ' ')
            return jsonify({'success': False, 'error': f'Translation failed for target={target_lang}. Text preview: "{preview}"'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    """Handle audio generation requests for translated text"""
    try:
        data = request.get_json(silent=True) or {}
        text = data.get('text', '')
        target_lang = data.get('target_lang', '')
        
        print(f"=== Audio Generation Request Debug ===")
        print(f"Text to convert to audio: {text[:100] if text else 'None'}...")
        print(f"Target language: {target_lang}")
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided for audio generation'})
        
        # Generate unique filename for audio
        unique_id = str(uuid.uuid4())[:8]
        out_name = f"translated_speech_{unique_id}.mp3"
        out_path = os.path.join(app.config['AUDIO_FOLDER'], out_name)
        
        # Ensure audio folder exists
        os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
        
        # Generate speech using TTS
        print(f"Generating audio for text length: {len(text)}")
        print(f"Using language: {target_lang}")
        ok = synthesize_speech(text, out_path, target_lang)
        
        if ok:
            # Store audio URL in session
            audio_url = url_for('static', filename=f'audio/{out_name}')
            session['audio_url'] = audio_url
            print(f"SUCCESS: Audio generated and stored: {audio_url}")
            return jsonify({'success': True, 'audio_url': audio_url})
        else:
            print("ERROR: TTS failed")
            return jsonify({'success': False, 'error': 'TTS failed. Check internet connection.'})
            
    except Exception as e:
        print(f"EXCEPTION in generate_audio route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/audio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(app.config['AUDIO_FOLDER'], filename, as_attachment=False)

@app.route('/test-tts')
def test_tts():
    """Test route to verify TTS is working"""
    try:
        test_text = "Hello, this is a test of text to speech."
        test_file = os.path.join(app.config['AUDIO_FOLDER'], 'test_speech.mp3')
        
        # Test TTS
        success = synthesize_speech(test_text, test_file, 'en')
        
        if success and os.path.exists(test_file):
            audio_url = url_for('static', filename='audio/test_speech.mp3')
            return f"""
            <h2>TTS Test Successful!</h2>
            <p>Audio file created: {test_file}</p>
            <p>File size: {os.path.getsize(test_file)} bytes</p>
            <audio controls src="{audio_url}"></audio>
            <p><a href="/">Back to main page</a></p>
            """
        else:
            return f"""
            <h2>TTS Test Failed</h2>
            <p>Success: {success}</p>
            <p>File exists: {os.path.exists(test_file) if 'test_file' in locals() else 'N/A'}</p>
            <p><a href="/">Back to main page</a></p>
            """
    except Exception as e:
        return f"""
        <h2>TTS Test Error</h2>
        <p>Error: {str(e)}</p>
        <p><a href="/">Back to main page</a></p>
        """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
