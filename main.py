import json
import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader

load_dotenv()

st.set_page_config(page_title="Flomind quiz", page_icon="🐥")

api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def get_best_model():
    try:
        active_model = None
        available_models = []

        # جلب قائمة الموديلات المتاحة لك
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                
                if 'flash' in m.name:
                    active_model = m.name
                    break
                
                elif 'pro' in m.name and not active_model:
                    active_model = m.name

        if not active_model and available_models:
            active_model = available_models[0]

        if active_model:
            print(f"✅ Selected Model: {active_model}")
            return active_model
        else:
            return None

    except Exception as e:
        print(f"⚠️ Error listing models: {e}")
        return "models/gemini-1.5-flash" 

#استخراج النص من ملف PDF
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

# توليد الأسئلة بناءً على النص المستخرج
def get_questions(text, number_of_questions=5):
    if not api_key:
        return None

    model_name = get_best_model()
    
    if not model_name:
        st.error("❌ No available models found for your API Key!")
        return None

    generation_config = {
        "temperature": 0.7,
        "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )

    prompt = f"""
    Act as a professional teacher. Generate {number_of_questions} multiple-choice questions (MCQ) based on the following text.
    
    IMPORTANT: Output MUST be valid JSON only.
    
    Structure:
    {{
        "questions": [
            {{
                "id": 1,
                "question": "Question text?",
                "options": ["A. Option", "B. Option", "C. Option", "D. Option"],
                "correct_answer": "A. Option",
                "explanation": "Why correct"
            }}
        ]
    }}

    Text:
    '''{text}'''
    """

    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Generation Error: {e}")
        return None


#الواجهة
def main():
    st.title("Flomind Quiz generator🐥🌸")
    st.write("Turn your PDFs into interactive quizzes instantly ✨")
    st.divider()

    if not api_key:
         st.warning("⚠️ Please add GOOGLE_API_KEY to your .env file")
         return

    with st.form(key="upload_file"):
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        number_of_questions = st.number_input("Number of questions", min_value=1, max_value=20, value=5)
        submit_button = st.form_submit_button(label="Generate Questions", type="primary")

        if submit_button:
            if uploaded_file is not None:
                with st.spinner("🔍 Finding best model & Generating Quiz..."):
                    text = extract_text_from_pdf(uploaded_file)
                    
                    response_json = get_questions(text, number_of_questions)
                    
                    if response_json:
                        questions = response_json.get("questions", [])
                        if questions:
                            st.success(f"Quiz Generated Successfully! 🎉")
                            for q in questions:
                                st.subheader(f"Q{q['id']}: {q['question']}")
                                for idx, option in enumerate(q["options"]):
                                    st.write(f"**{option}**")
                                with st.expander("Show Answer"):
                                    st.info(f"**Correct Answer:** {q['correct_answer']}")
                                    st.write(f"**Explanation:** {q['explanation']}")
                        else:
                            st.error("No questions found in response.")
                    else:
                        st.error("Failed to generate questions.")
            else:
                st.warning("Please upload a PDF file first.")


if __name__ == '__main__':
    main()