"""Extract ground-truth text from the clean vector PDFs (selectable text)."""
import pypdfium2 as pdfium


def extract_reference_text(pdf_path) -> str:
    pdf = pdfium.PdfDocument(str(pdf_path))
    pages_text = []
    for page in pdf:
        textpage = page.get_textpage()
        pages_text.append(textpage.get_text_range())
    return "\n".join(pages_text)
