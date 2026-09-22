"""Thin wrapper around PaddleOCR for scanned invoice images.

Pinned to paddlepaddle==2.6.2 / paddleocr==2.7.3 (the newer 3.x stack's
PIR inference backend crashes on this machine — see docs/eval report).
Run this module's caller from the dedicated `.venv-paddle` environment
(Python 3.12; paddlepaddle has no wheel for 3.14).
"""
from paddleocr import PaddleOCR

_ENGINES = {}


def _get_engine(lang: str) -> PaddleOCR:
    if lang not in _ENGINES:
        _ENGINES[lang] = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    return _ENGINES[lang]


def run_paddleocr(image_path, lang: str = "fr") -> str:
    engine = _get_engine(lang)
    result = engine.ocr(str(image_path), cls=True)
    lines = result[0] or []
    return "\n".join(text for _box, (text, _score) in lines)
