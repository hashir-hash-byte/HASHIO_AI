import streamlit as st
import google.generativeai as genai

# 1. Setup the Title and Description
st.title("📚 HASHIO_AI: VTU Notes & File Summarizer")
st.write("Welcome, Mohammed! Paste your notes or drop a file below to get an intelligent AI summary.")

# 2. Automatically load the API Key from Streamlit's secure vault
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key missing! Please configure GEMINI_API_KEY in the Streamlit Secrets panel.")
    st.stop()

# 3. Create two tabs: One for text input, one for file uploads
tab1, tab2 = st.tabs(["📝 Paste Text", "📁 Upload File"])

notes_to_analyze = ""

with tab1:
    user_notes = st.text_area("Paste your VTU Notes here:", height=250, key="text_input")
    if user_notes:
        notes_to_analyze = user_notes

with tab2:
    uploaded_file = st.file_uploader("Upload a text file (.txt):", type=["txt"])
    if uploaded_file is not None:
        # Read the file contents as text strings
        file_contents = uploaded_file.read().decode("utf-8")
        st.success(f"Successfully loaded: {uploaded_file.name}")
        # Show a quick preview of what's inside the file
        with st.expander("Preview uploaded file content"):
            st.code(file_contents[:500] + "...", language="text")
        notes_to_analyze = file_contents

# 4. Process the text when the button is clicked
if st.button("Generate AI Summary"):
    if not notes_to_analyze.strip():
        st.warning("Please paste some notes or upload a file first!")
    else:
        with st.spinner("AI is analyzing and summarizing your notes..."):
            try:
                # Initialize the recommended active model
                model = genai.GenerativeModel('gemini-3.5-flash')
                
                # Craft a precise engineering prompt for the model
                prompt = (
                    f"You are an expert engineering professor. Summarize the following "
                    f"academic notes or document. Break down the core concepts into clear, concise bullet points "
                    f"that are easy to study for exams:\n\n{notes_to_analyze}"
                )
                
                # Generate content
                response = model.generate_content(prompt)
                
                # Display the real summary
                st.subheader("📝 AI-Generated Summary:")
                st.success(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
