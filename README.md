📚 AI Knowledge Assistant

An AI-powered backend system that allows users to upload documents (PDF/TXT) and ask intelligent, context-aware questions about their content.
This project combines FastAPI, LLMs (Groq), OCR fallback, and vector-based retrieval to handle both text-based and scanned documents reliably.
Built to behave like an academic assistant — not a generic chatbot.

🚀 What This Project Does

•Upload PDFs or TXT files
•Automatically extract text
•Uses standard PDF parsing
•Falls back to OCR for scanned PDFs
•Splits content into semantic chunks
•Stores embeddings in a vector store
•Answers questions using LLM + document context

Handles:

•Question papers
•Notes
•Books
•Reports

🧠 Key Features

✅ Smart Text Extraction
•Text-based PDFs → parsed normally
•Scanned PDFs → OCR fallback (Tesseract + pdf2image)
•Automatic detection of low-text PDFs

✅ Academic-Aware Answering
Distinguishes between:
•Question papers (answers may not exist in PDF)
•Notes/books (answers must come from document)
•Exam-safe, structured responses
•No hallucinated sections

✅ Code-Safe LLM Output
•Generates correct, complete code when asked
•Detects programming language automatically
•No unnecessary explanations unless requested

✅ Backend-First Design
•Clean FastAPI architecture
•Easy to integrate with any frontend (Streamlit / React / etc.)

🛠️ Tech Stack
•Backend: FastAPI
•LLM: Groq (LLaMA 3.1)
•OCR: Tesseract + pdf2image
•PDF Parsing: pypdf
•Embeddings: Vector store (local)
•Environment Management: python-dotenv

📦 Project Structure
ai-knowledge-assistant/
│
├── app/
│   ├── main.py
│   ├── routes/
│   │   └── upload.py
│   └── services/
│       ├── file_parser.py
│       ├── embeddings.py
│       ├── vector_store.py
│       └── llm.py
│
├── streamlit_app/        
│
├── requirements.txt
├── .gitignore
└── README.md

⚙️ Local Setup (Recommended Way)
1️⃣ Clone the Repository
git clone https://github.com/Manas-Sharma-210/ai-knowledge-assistant.git
cd ai-knowledge-assistant

2️⃣ Create Virtual Environment
python -m venv venv

Activate it:

Windows (PowerShell / CMD)
venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Set Environment Variables
Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here

5️⃣ (Optional) OCR Setup (Windows)
If you want OCR support for scanned PDFs:
•Install Tesseract OCR
•Install Poppler
•Update the Poppler path inside file_parser.py if needed
•OCR is automatically used only when required.

6️⃣ Run the Backend
uvicorn app.main:app --reload

Backend will be live at:
http://127.0.0.1:8000

📡 API Endpoints (Overview)
•POST /upload → Upload document
•POST /answer → Ask questions
•POST /reset → Clear session data
(Designed to be frontend-agnostic)

🧪 Example Use Cases
-Ask questions from university notes
-Solve questions from scanned question papers
-Extract academic details from PDFs
-Use as backend for:
 •Streamlit app
 •React frontend
 •College projects

 🧭 Current Status

✅ Fully working locally
❌ Cloud deployment deferred (OCR + system dependencies)
📌 Designed to be deployment-ready with containerization later

👤 Author
Manas Sharma
