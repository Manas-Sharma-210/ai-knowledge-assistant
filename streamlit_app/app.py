import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="📘",
    layout="centered"
)

st.title("📘 AI Knowledge Assistant")

# =========================
# PERSISTENT STATE (SURVIVES REFRESH)
# =========================
@st.cache_data(show_spinner=False)
def load_state():
    return {
        "uploaded": False,
        "messages": [],
        "last_file_name": None
    }

@st.cache_data(show_spinner=False)
def save_state(state):
    return state

state = load_state()

# Initialize session state from cache
if "uploaded" not in st.session_state:
    st.session_state.uploaded = state["uploaded"]

if "messages" not in st.session_state:
    st.session_state.messages = state["messages"]

if "last_file_name" not in st.session_state:
    st.session_state.last_file_name = state["last_file_name"]

# =========================
# STREAMING HELPER
# =========================
def stream_text(text, delay=0.05):
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)

# =========================
# FILE UPLOAD
# =========================
st.subheader("Upload a document (PDF or TXT)")

uploaded_file = st.file_uploader(
    "Upload file",
    type=["pdf", "txt"]
)

# =========================
# AI DISCLAIMER (NEW – OPTION B)
# =========================
with st.expander("ℹ️ About this assistant"):
    st.markdown(
        """
        This assistant helps you understand uploaded documents and answer questions based on their content.

For question papers, it uses standard academic knowledge to answer questions correctly.
For notes, books, or reports, it relies primarily on the uploaded document.

Minor formatting issues may occur due to PDF extraction.
For exact wording, ask for verbatim text and always verify important details from the original file.
        """
    )

#FILE REMOVED → HARD RESET (ONLY HERE)
if uploaded_file is None and st.session_state.uploaded:
    st.session_state.uploaded = False
    st.session_state.messages = []
    st.session_state.last_file_name = None

    st.cache_data.clear()  # clear persistence

    try:
        requests.post(f"{BACKEND_URL}/reset")
    except Exception:
        pass

    st.info("Document removed. Upload a new document to start fresh.")

#FILE UPLOADED / CHANGED
elif uploaded_file is not None:
    if uploaded_file.name != st.session_state.last_file_name:
        with st.spinner("Uploading and processing document..."):
            response = requests.post(
                f"{BACKEND_URL}/upload",
                files={"file": (uploaded_file.name, uploaded_file.getvalue())}
            )

        if response.status_code == 200:
            st.success("Document uploaded successfully!")
            st.session_state.uploaded = True
            st.session_state.messages = []
            st.session_state.last_file_name = uploaded_file.name
        else:
            st.error("Upload failed.")
            st.stop()

# =========================
# CHAT HISTORY
# =========================
st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# CHAT INPUT
# =========================
if st.session_state.uploaded:
    user_input = st.chat_input("Ask a question about the document...")

    if user_input:
        # USER MESSAGE
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        payload = {
            "question": user_input,
            "mode": "qa",
            "language": "english"
        }

        # ASSISTANT (STREAMING)
        with st.chat_message("assistant"):
            placeholder = st.empty()

            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{BACKEND_URL}/answer",
                    json=payload
                )

            if response.status_code == 200:
                full_answer = response.json().get("answer", "")
            else:
                full_answer = "Something went wrong."

            streamed = ""
            for chunk in stream_text(full_answer):
                streamed += chunk
                placeholder.markdown(streamed)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_answer
        })

else:
    st.info("Upload a document to start chatting.")

# =========================
# SAVE STATE (IMPORTANT)
# =========================
save_state({
    "uploaded": st.session_state.uploaded,
    "messages": st.session_state.messages,
    "last_file_name": st.session_state.last_file_name
})
