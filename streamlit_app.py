import streamlit as st
import requests
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api"

st.set_page_config(page_title="ContextAI (Streamlit Demo)", page_icon="🤖")

st.title("🤖 ContextAI (Streamlit Demo)")
st.markdown("---")

# Sidebar for File Upload
with st.sidebar:
    st.header("📄 Document Upload")
    uploaded_file = st.file_uploader("Upload a PDF to start", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing PDF..."):
                try:
                    # Prepare file for upload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        st.success(f"✅ Successfully processed: {uploaded_file.name}")
                        st.session_state['current_file'] = uploaded_file.name
                    else:
                        st.error(f"❌ Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"⚠️ Error connecting to backend: {str(e)}")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call Backend API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json={"question": prompt}
            )
            
            if response.status_code == 200:
                data = response.json()
                full_response = data.get("answer", "No response from AI.")
                
                # Add sources if available
                sources = data.get("sources", [])
                if sources:
                    full_response += f"\n\n**Sources:** {', '.join(sources)}"
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_msg = f"Error: Backend returned {response.status_code}"
                message_placeholder.markdown(error_msg)
        except Exception as e:
            message_placeholder.markdown(f"⚠️ Error: Could not connect to backend. {str(e)}")
