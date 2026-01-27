from fastapi import APIRouter, UploadFile, File, Body
import os

from app.services.file_parser import extract_text, chunk_text
from app.services.embeddings import EmbeddingModel
from app.services.vector_store import VectorStore
from app.services.llm import LLM

# =========================
# INITIALIZATION
# =========================

router = APIRouter()

embedder = EmbeddingModel()
vector_store = VectorStore()
llm = LLM()

UPLOAD_DIR = "app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# =========================
# CONTEXT LIMITER 
# =========================
def limit_context(chunks: list[str], max_chars: int = 12000) -> str:
    collected = []
    total = 0

    for chunk in chunks:
        if total + len(chunk) > max_chars:
            break
        collected.append(chunk)
        total += len(chunk)

    return "\n\n".join(collected)

# =========================
# RESET MEMORY
# =========================
@router.post("/reset")
async def reset_memory():
    vector_store.reset()
    return {"status": "vector memory cleared"}

# =========================
# UPLOAD DOCUMENT
# =========================
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    vector_store.reset()

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    extracted_text = extract_text(file_path)

    if not extracted_text.strip():
        return {"error": "No readable text found in document."}

    chunks = chunk_text(extracted_text)
    embeddings = embedder.embed_texts(chunks)

    vector_store.add_documents(chunks, embeddings)

    return {
        "filename": file.filename,
        "characters": len(extracted_text),
        "total_chunks": len(chunks),
        "stored_in_vector_db": True
    }

# =========================
# RECALL (DEBUG)
# =========================
@router.post("/recall")
async def recall_from_memory(query: str = Body(...)):

    query_embedding = embedder.embed_texts([query])[0]

    results = vector_store.search(
        query_embedding=query_embedding,
        top_k=8
    )

    return {
        "query": query,
        "recalled_chunks": results["documents"][0]
    }

# =========================
# ANSWER / NOTES / SUMMARY
# =========================
@router.post("/answer")
async def answer_from_document(payload: dict = Body(...)):

    question: str = payload.get("question", "").strip()
    mode: str = payload.get("mode", "qa")
    language: str = payload.get("language", "english")

    # =========================
    # LANGUAGE RULES
    # =========================
    if language == "hinglish":
        language_instruction = """
Use natural Hinglish (Hindi + English mix).
Friendly, clear, knowledgeable tone.
"""
    elif language == "hindi":
        language_instruction = """
Explain in simple conversational Hindi.
Suitable for college exams.
"""
    else:
        language_instruction = """
Explain in clear, concise English.
Exam-appropriate tone.
"""

    # =========================
    # VERBATIM INTENT DETECTION
    # =========================
    VERBATIM_KEYWORDS = [
        "exact", "exact content", "exact text",
        "word by word", "verbatim",
        "exactly as written", "what is written",
        "entire page", "full page",
        "candidate declaration", "declaration page"
    ]

    is_verbatim = any(kw in question.lower() for kw in VERBATIM_KEYWORDS)

    # ======================================================
    # ADDED: FACTUAL QUESTION GUARD (VERY IMPORTANT)
    # ======================================================
    FACTUAL_PATTERNS = [
        "how many", "how much",
        "how many parts", "how many sections",
        "which part", "which section",
        "total marks", "maximum marks",
        "number of questions", "how many questions"
    ]

    is_factual_query = any(
        kw in question.lower() for kw in FACTUAL_PATTERNS
    )

    # ======================================================
    # META QUERY DETECTION (SAFE)
    # ======================================================
    META_KEYWORDS = [
        "help me understand",
        "explain this paper",
        "walk me through",
        "go through this paper",
        "can you help me"
    ]

    is_meta_query = (
        any(kw in question.lower() for kw in META_KEYWORDS)
        and not is_factual_query   #  ADDED GUARD
    )

    # ======================================================
    # META QUERY HANDLING (EARLY EXIT)
    # ======================================================
    if is_meta_query:
        prompt = f"""
The user is asking for guidance, not direct answers.

Rules:
- Do NOT dump all questions
- Do NOT repeat content
- Offer 2–3 clear options
- Ask the user to choose ONE option
- STOP after that

User question:
{question}
"""
        answer = llm.generate(prompt)

        return {
            "question": question,
            "mode": mode,
            "language": language,
            "answer": answer
        }

    # =========================
    # GLOBAL QUERY DETECTION
    # =========================
    GLOBAL_KEYWORDS = [
        "whole pdf", "entire pdf",
        "whole document", "entire document",
        "all subjects", "list all",
        "complete list", "total subjects"
    ]

    is_global_query = any(
        kw in question.lower() for kw in GLOBAL_KEYWORDS
    )

    # =========================
    # CONTEXT RETRIEVAL
    # =========================
    if is_verbatim:
        context_chunks = vector_store.search_all(limit=80)

    elif is_global_query or mode == "summary":
        context_chunks = vector_store.search_all(limit=50)

    else:
        if not question:
            return {"error": "Question is required."}

        query_embedding = embedder.embed_texts([question])[0]
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=8
        )
        context_chunks = results["documents"][0]

    if not context_chunks:
        return {
            "question": question,
            "answer": "Is document mein is question se related information nahi hai."
        }

    context = limit_context(context_chunks)

    # =========================
    # PROMPT SELECTION
    # =========================
    if is_verbatim:
        prompt = f"""
Reproduce the following document text EXACTLY as it appears.

{language_instruction}

Document Content:
{context}

Question:
{question}
"""

    elif mode == "summary":
        prompt = f"""
Summarize the document using ONLY the provided content.

{language_instruction}

Content:
{context}
"""

    elif mode == "short_notes":
        prompt = f"""
Create short exam-oriented notes.

{language_instruction}

Content:
{context}
"""

    elif mode == "long_notes":
        prompt = f"""
Create detailed exam-ready notes.

{language_instruction}

Content:
{context}
"""

    elif mode == "bullets":
        prompt = f"""
Convert the content into clean bullet points.

{language_instruction}

Content:
{context}
"""

    else:
        prompt = f"""
Answer the question using ONLY the document content.

{language_instruction}

Context:
{context}

Question:
{question}
"""

    # =========================
    # GENERATE ANSWER
    # =========================
    answer = llm.generate(prompt)

    # =========================
    # VERBATIM OUTPUT ANNOTATION
    # =========================
    if is_verbatim:
        answer = (
            "⚠ NOTE: Text reproduced directly from PDF.\n\n"
            + answer
        )

    return {
        "question": question,
        "mode": mode,
        "language": language,
        "answer": answer
    }

