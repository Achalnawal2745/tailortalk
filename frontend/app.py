import streamlit as st
import requests
import uuid
import time

# --- Page Config ---
st.set_page_config(
    page_title="TailorTalk | Drive Agent",
    page_icon="📂",
    layout="centered"
)

# --- Custom CSS for Premium Look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #0e1117;
    }
    
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    
    /* Chat Bubble Styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stChatMessage[data-testid="stChatMessageUser"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
    }
    
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Header Styling */
    .header-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    h1 {
        font-weight: 800 !important;
        font-size: 3rem !important;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- Backend URL ---
# In production, this would be your Railway/Render URL
BACKEND_URL = st.sidebar.text_input("Backend URL", "http://localhost:8000")

# --- Session State ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your TailorTalk Drive Agent. How can I help you find files today?"}
    ]

# --- UI Layout ---
st.markdown('<div class="header-container"><h1>TailorTalk</h1></div>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">AI-Powered File Discovery for Google Drive</p>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Search for 'Financial reports from last week' or 'Project JPGs'..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Backend
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔍 Searching your Drive...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json={"user_id": st.session_state.user_id, "message": prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                full_response = response.json()["response"]
                # Simulate streaming for premium feel
                displayed_text = ""
                for char in full_response:
                    displayed_text += char
                    message_placeholder.markdown(displayed_text + "▌")
                    time.sleep(0.005)
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = f"Error: {response.status_code} - {response.text}"
                message_placeholder.error(error_msg)
        except Exception as e:
            message_placeholder.error(f"Failed to connect to backend: {str(e)}")

# Sidebar info
with st.sidebar:
    st.title("Settings & Info")
    st.info("""
    **Tips for searching:**
    - "Find PDFs modified yesterday"
    - "Search for 'Invoice' in filenames"
    - "Look for documents containing 'Project X'"
    """)
    if st.button("Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared. How can I help you now?"}
        ]
        st.rerun()
