from pypdf import PdfReader
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

# CORRECT POPPLER PATH (FOUND VIA where.exe)
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"

# Inject into PATH so subprocess can find pdfinfo.exe
os.environ["PATH"] += os.pathsep + POPPLER_PATH

def extract_text(file_path: str) -> str:
    """
    Detect file type and extract text.
    Automatically falls back to OCR for scanned PDFs.
    ALSO boosts important academic lines so RAG doesn't miss them.
    """

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        text = _extract_pdf(file_path)

        #  OCR FALLBACK (scanned PDFs)
        if len(text.strip()) < 500:
            print("[INFO] Low text detected, switching to OCR...")
            text = _extract_pdf_with_ocr(file_path)

    elif ext == ".txt":
        text = _extract_txt(file_path)

    else:
        raise ValueError("Unsupported file type.")

    if not text.strip():
        raise ValueError("No extractable text found in document.")

    #  Academic signal boosting (UNCHANGED)
    important_lines = []
    for line in text.split("\n"):
        l = line.lower()
        if (
            "semester" in l
            or "year" in l
            or "session" in l
            or "effective from" in l
            or "admitted" in l
        ):
            important_lines.append(line.strip())

    boosted_text = "\n".join(important_lines) + "\n\n" + text
    return clean_text(boosted_text)


def _extract_pdf(file_path: str) -> str:
    """
    Extract text from text-based PDFs using pypdf.
    """

    reader = PdfReader(file_path)
    text = ""

    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        except Exception as e:
            print(f"[WARN] Failed to extract page {i}: {e}")
            continue

    return clean_text(text)


def _extract_pdf_with_ocr(file_path: str) -> str:
    """
    OCR extraction for scanned PDFs.
    Converts PDF pages to images and extracts text using Tesseract.
    """

    pages = convert_from_path(
    file_path,
    dpi=300,
    poppler_path=POPPLER_PATH,
    use_pdftocairo=False
)


    text = ""

    for i, page in enumerate(pages):
        try:
            page_text = pytesseract.image_to_string(page, lang="eng")
            if page_text:
                text += page_text + "\n"
        except Exception as e:
            print(f"[OCR WARN] Failed on page {i}: {e}")
            continue

    return clean_text(text)


def _extract_txt(file_path: str) -> str:
    """
    Extract text from plain text files.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return clean_text(f.read())


def clean_text(text: str) -> str:
    """
    Basic text normalization for AI processing.
    Keeps content intact, only removes noise.
    """

    # Remove excessive newlines
    while "\n\n" in text:
        text = text.replace("\n\n", "\n")

    # Remove extra spaces
    while "  " in text:
        text = text.replace("  ", " ")

    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 80
) -> list[str]:
    """
    Split text into overlapping chunks for embeddings.
    Overlap preserves context between chunks.
    """

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end]
        chunks.append(chunk)

        if end == length:
            break

        start = end - overlap
        if start <= 0:
            start = end

    return chunks
