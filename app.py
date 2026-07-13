import streamlit as st
import google.generativeai as genai

# 1. Setup the Title and Description
st.title("📚 VTU Notes Summarizer (v2.0)")
st.write("Welcome, Mohammed! Paste your engineering notes below to get an intelligent AI summary.")

# 2. Add an input box for your API Key in the sidebar so it's clean
with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input("Enter your Gemini API Key:", type="password")
    st.info("Get a free key from Google AI Studio")

# 3. Text area for your VTU Notes
user_notes = st.text_area("Paste your VTU Notes here:", height=250)

# 4. Process the text when the button is clicked
if st.button("Generate AI Summary"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar first!")
    elif user_notes.strip() == "":
        st.warning("Please paste some notes to summarize!")
    else:
        with st.spinner("AI is analyzing and summarizing your notes..."):
            try:
                # Configure the legacy library with your key
                genai.configure(api_key=api_key)
                
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
