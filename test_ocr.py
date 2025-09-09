import pytesseract
from PIL import Image

# Optional: set path to Tesseract if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

print("Tesseract version:", pytesseract.get_tesseract_version())

# Create a test image with text
from PIL import ImageDraw, ImageFont
img = Image.new("RGB", (300, 100), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10, 40), "Hello OCR!", fill=(0, 0, 0))
img.save("sample.png")

# Run OCR
text = pytesseract.image_to_string(Image.open("sample.png"))
print("OCR Output:", text)
