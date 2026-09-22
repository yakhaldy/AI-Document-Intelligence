"""Thin wrapper around Tesseract for scanned invoice images."""
import pytesseract
from PIL import Image


def run_tesseract(image_path, lang: str = "fra") -> str:
    image = Image.open(image_path)
    return pytesseract.image_to_string(image, lang=lang)
