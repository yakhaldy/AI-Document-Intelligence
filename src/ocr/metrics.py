"""Character Error Rate (CER) between OCR output and reference text."""
import jiwer


def compute_cer(reference: str, hypothesis: str) -> float:
    return jiwer.cer(reference, hypothesis)
