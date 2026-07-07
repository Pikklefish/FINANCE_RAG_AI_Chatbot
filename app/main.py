import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from app.config import Config
from app.ingestor import DocumentIngestor
from app.rag_pipeline import RAGPipeline
from app.hallucination import HallucinationChecker

# 1. Page config
# ── Page config — must be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="Finance RAG Chatbot",
    page_icon="📊",
    layout="wide"
)

# 2. Validate config
# ── Validate config ───────────────────────────────────────────────────────────
try:
    Config.validate()
except EnvironmentError as e:
    st.error(f"🔴 {e}")
    st.stop()

# 3. Get session_id
ctx = get_script_run_ctx()
session_id = ctx.session_id if ctx else "default_session"

# 4. Initialise session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "ingestor" not in st.session_state:
    st.session_state.ingestor = None  # wait till pdf uploaded

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None  # wait till pdf uploaded

if "checker" not in st.session_state:
    st.session_state.checker = HallucinationChecker()

# 5. Sidebar — file uploader
with st.sidebar:
    st.title("📂 Upload Document")
    
    uploaded_file = st.file_uploader(
        "Upload a financial PDF",
        type=["pdf"]
    )
    
    if uploaded_file is not None:
        #only ingest new files
        if st.session_state.ingestor is None:
            with st.spinner("Ingesting document ..."):
                
                #create ingestor + ingest
                ingestor = DocumentIngestor()
                chunk_count = ingestor.ingest(uploaded_file)
                st.session_state.ingestor = ingestor
                
                #creae pipeline using vectorstore
                st.session_state.pipeline = RAGPipeline(
                    ingestor.get_vectorstore()
                )
            
            st.success(f"✅ Ready! Ingested {chunk_count} chunks.")
    
    #Show status
    if st.session_state.pipeline is not None:
        st.info("🟢 Document loaded — ask your questions!")
    else:
        st.warning("⬆️ Please upload a PDF to begin.")
    
# 6. Main area — chat interface
st.title("📊 Finance RAG Chatbot")
st.caption("Ask questions grounded in your uploaded financial document.")
# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
        # if assistant message has a warning, show it
        if message["role"] == "assistant" and message.get("warning"):
            st.warning(message["warning"])
        
        # if assistant message has sources, show them
        if message["role"] == "assistant" and message.get("sources"):
            st.markdown(message["sources"])

# 7. Handle user input
user_input = st.chat_input(
    "Ask a question about your document...",
    disabled=st.session_state.pipeline is None
)

if user_input:
    # Step 1: guard check
    if st.session_state.pipeline is None:
        st.warning("Please upload a PDF first.")
        st.stop()
    # Step 2: display + save user message
    with st.chat_message("human"):
        st.write(user_input)
    
    st.session_state.messages.append({
        "role": "human",
        "content": user_input,
    })
    
    # Step 3: query pipeline
    with st.spinner("Thinking ..."):
        result = st.session_state.pipeline.query(
            question = user_input,
            session_id = session_id
        )
        answer = result["answer"]
        source_docs = result["sources"]
    
    # Step 4: hallucination check
    status, warning = st.session_state.checker.check(
        answer,
        source_docs
    )
    
    # Step 5: format citations
    formatted_sources = st.session_state.checker.format_sources(source_docs)
    
    # Step 6: display + save assistant message
    with st.chat_message("assistant"):
        st.write(answer)
        if warning:
            st.warning(warning)
        
        if formatted_sources:
            st.markdown(formatted_sources)
            
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "warning": warning,
        "sources": formatted_sources
    })