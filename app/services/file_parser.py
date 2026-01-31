from pypdf import PdfReader
from pathlib import Path
import os

# ============================================================
# OPTIONAL OCR IMPORTS
# ============================================================
try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None

try:
    from PIL import Image
except ImportError:
    Image = None

# ============================================================
# OCR TOGGLE (🔥 ADDED — SAFE, NON-DESTRUCTIVE)
# ============================================================
ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"

# ============================================================
# POPPLER PATH (WINDOWS ONLY)
# ============================================================
POPPLER_PATH = r"C:\poppler\poppler-25.12.0\Library\bin"
if os.path.exists(POPPLER_PATH):
    os.environ["PATH"] += os.pathsep + POPPLER_PATH


def extract_text(file_path: str) -> str:
    """
    Detect file type and extract text.
    Falls back to OCR for scanned PDFs.
    """

    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        text = _extract_pdf(file_path)

        # ====================================================
        # OCR fallback for scanned PDFs (🔥 FIXED + TOGGLED)
        # ====================================================
        if len(text.strip()) < 500:
            print("[INFO] Low text detected.")
            if ENABLE_OCR and pytesseract and convert_from_path:
                print("[INFO] OCR enabled, switching to OCR...")
                text = _extract_pdf_with_ocr(file_path)
            else:
                print("[WARN] OCR disabled or unavailable. Skipping OCR.")

    elif ext == ".txt":
        text = _extract_txt(file_path)

    else:
        raise ValueError("Unsupported file type.")

    if not text.strip():
        raise ValueError("No extractable text found in document.")

    # ============================================================
    # Academic signal boosting (UNCHANGED)
    # ============================================================
    important_lines = []
    for line in text.split("\n"):
        l = line.lower()
        if any(k in l for k in [
            "semester", "year", "session",
            "effective from", "admitted"
        ]):
            important_lines.append(line.strip())

    boosted_text = "\n".join(important_lines) + "\n\n" + text
    return clean_text(boosted_text)


def _extract_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""

    for i, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        except Exception as e:
            print(f"[WARN] Failed page {i}: {e}")

    return clean_text(text)


def _extract_pdf_with_ocr(file_path: str) -> str:
    # ============================================================
    # HARD SAFETY CHECK (UNCHANGED)
    # ============================================================
    if not (pytesseract and convert_from_path):
        return ""

    pages = convert_from_path(
        file_path,
        dpi=300,
        poppler_path=POPPLER_PATH if os.path.exists(POPPLER_PATH) else None
    )

    text = ""
    for i, page in enumerate(pages):
        try:
            page_text = pytesseract.image_to_string(page, lang="eng")
            if page_text:
                text += page_text + "\n"
        except Exception as e:
            print(f"[OCR WARN] Page {i}: {e}")

    return clean_text(text)


def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return clean_text(f.read())


def clean_text(text: str) -> str:
    while "\n\n" in text:
        text = text.replace("\n\n", "\n")
    while "  " in text:
        text = text.replace("  ", " ")
    return text.strip()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(text[start:end])
        if end == length:
            break
        start = max(0, end - overlap)

    return chunks
