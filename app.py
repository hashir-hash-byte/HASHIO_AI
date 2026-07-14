import streamlit as st
import google.generativeai as genai
import cohere
from gtts import gTTS
import io
from datetime import datetime

# 1. Setup Streamlit Page Configurations
st.set_page_config(page_title="HASHIO_AI Engine", page_icon="🤖", layout="centered")
st.title("🤖 HASHIO_AI Platform")

# Configure the backup Gemini engine using credentials from settings
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Initialize rolling conversation visual memory array if missing
if "messages" not in st.session_state:
    st.session_state.messages = []
if "username" not in st.session_state:
    st.session_state.username = "Developer"

# 2. Render Historical Chat Elements From Current Session State
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Handle Live Incoming User Prompt Inputs
if final_prompt := st.chat_input("Ask HASHIO_AI anything..."):
    
    # Render user message container visually on screen
    with st.chat_message("user"):
        st.markdown(final_prompt)
    
    # Commit user prompt to persistent visual memory loop
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    
    # Process Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_response = None
            
            # --- ENGINE A: TRY COHERE flagship MODEL ---
            try:
                cohere_key = st.secrets.get("COHERE_API_KEY", None)
                if cohere_key:
                    co_client = cohere.ClientV2(api_key=cohere_key)
                    
                    system_context = "You are an expert engineering mentor. Answer clearly and split dense technical explanations into easy-to-read bullet points."
                    
                    # Package chat history for Cohere's structure payload
                    messages_payload = [{"role": "system", "content": system_context}]
                    for m in st.session_state.messages[:-1]:
                        messages_payload.append({"role": m["role"], "content": m["content"]})
                    messages_payload.append({"role": "user", "content": final_prompt})
                    
                    response = co_client.chat(
                        model="command-r-plus",
                        messages=messages_payload
                    )
                    ai_response = response.message.content
                    source_label = "Cohere (Command-R+)"
            except Exception as co_err:
                st.warning("Cohere engine rate limit hit. Shifting to backup framework...")
            
            # --- ENGINE B: BACKUP FALLBACK TO GOOGLE GEMINI ---
            if not ai_response:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    system_context = "You are an expert engineering mentor. Answer clearly and split dense technical explanations into easy-to-read bullet points.\n\n"
                    history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
                    full_payload = f"{system_context}{history_context}\nuser: {final_prompt}"
                    
                    response = model.generate_content(full_payload)
                    ai_response = response.text
                    source_label = "Google Gemini"
                except Exception as e:
                    st.error(f"Critical System Failure: Both AI engines are down. Details: {e}")
            
            # --- RENDER OUTPUT AND GENERATE COMPONENT UTILITIES ---
            if ai_response:
                st.markdown(ai_response)
                
                # Append finalized assistant text data block to rolling memory state
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                # On-demand Audio Player Component Setup
                button_key = f"audio_{datetime.now().strftime('%H%M%S')}"
                if st.button("🔊 Generate Audio Track", key=button_key):
                    with st.spinner("Converting text to speech..."):
                        speech_text = ai_response.replace("*", "").replace("-", " ")
                        tts = gTTS(text=speech_text, lang='en', tld='com')
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        fp.seek(0)
                        st.audio(fp, format="audio/mp3")
