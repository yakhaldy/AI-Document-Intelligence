FROM python:3.12-slim

# tesseract-ocr : binaire requis par pytesseract (pas un simple binding Python)
# tesseract-ocr-fra : pack de langue française utilisé par l'OCR (README §2.2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY db ./db
RUN pip install --no-cache-dir -e .

COPY alembic.ini ./

RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data/uploads \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
