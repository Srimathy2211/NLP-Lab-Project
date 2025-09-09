# Translation Feature Guide

## How to Use Translation

1. **Upload your document** (PDF, DOCX, TXT, or image)
2. **Check the "Translate to" checkbox**
3. **Enter the target language code** (e.g., `hi` for Hindi, `ta` for Tamil)
4. **Click "Upload → Listen"**

## Supported Language Codes

- `hi` - Hindi
- `ta` - Tamil  
- `es` - Spanish
- `fr` - French
- `de` - German
- `en` - English
- And many more supported by the M2M100 model

## What You'll See

After successful translation, you'll see:
- **Translated Text** - The text in your target language
- **Original Text** - A preview of the source text
- **Audio Player** - Listen to the translated text
- **Language Badges** - Shows source and target languages

## Troubleshooting

### Translation Not Working?

1. **Check your internet connection** - The translation model needs to download
2. **Verify language codes** - Use 2-letter ISO codes (e.g., `hi`, not `hindi`)
3. **Check console logs** - Look for error messages in the terminal
4. **Try different languages** - Some language pairs work better than others

### Common Issues

- **"Translation failed" message**: The model couldn't process your text
- **No translated text displayed**: Check if translation checkbox is checked
- **Slow performance**: First-time translation takes longer due to model download

### Testing Translation

Run the test script to verify translation works:
```bash
python test_translation.py
```

## Technical Details

- **Translation Engine**: Facebook M2M100 multilingual model
- **Model Size**: ~1.2GB (downloads automatically on first use)
- **Supported Formats**: Text from PDFs, DOCX, images (OCR), plain text
- **Fallback**: If translation fails, original text is used for audio

## Getting Help

If you continue to have issues:
1. Check the terminal/console for error messages
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Try with a simple English text first to test the system
