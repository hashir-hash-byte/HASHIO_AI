import streamlit as st
import google.generativeai as genai

# 1. Setup the Title and Description
st.title("📚 HASHIO_AI: VTU Notes Summarizer")
st.write("Welcome, Mohammed! Paste your engineering notes below to get an intelligent AI summary.")

# 2. Automatically load the API Key from Streamlit's secure vault
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API Key missing! Please configure GEMINI_API_KEY in the Streamlit Secrets panel.")
    st.stop()

# 3. Text area for your VTU Notes
user_notes = st.text_area("Paste your VTU Notes here:", height=250)

# 4. Process the text when the button is clicked
if st.button("Generate AI Summary"):
    if user_notes.strip() == "":
        st.warning("Please paste some notes to summarize!")
    else:
        with st.spinner("AI is analyzing and summarizing your notes..."):
            try:
                # Initialize the recommended active model
                model = genai.GenerativeModel('gemini-3.5-flash')
                
                # Craft a precise engineering prompt for the model
                prompt = (
                    f"You are an expert engineering professor. Summarize the following "
                    f"academic notes. Break down the core concepts into clear, concise bullet points "
                    f"that are easy to study for exams:\n\n{user_notes}"
                )
                
                # Generate content
                response = model.generate_content(prompt)
                
                # Display the real summary
                st.subheader("📝 AI-Generated Summary:")
                st.success(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
