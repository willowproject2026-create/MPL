import streamlit as st
import google.generativeai as genai
import PyPDF2

# Frontend UI Design - Vertical Layout
st.set_page_config(page_title="Specs Procurement Extractor", layout="centered")

st.title("Construction Specs Procurement Extractor")
st.markdown("Upload a CSI MasterFormat specification file to automatically generate a categorized procurement log.")

# Vertical input sections
api_key = st.text_input("Google Gemini API Key", type="password", placeholder="Enter your free API Key")
uploaded_file = st.file_uploader("Upload Specification PDF", type=["pdf"])

# Processing logic
if st.button("Process Specifications", type="primary"):
    if not api_key:
        st.error("Error: Please provide a Gemini API Key to process the document.")
    elif not uploaded_file:
        st.error("Error: Please upload a specification PDF file.")
    else:
        with st.spinner("Analyzing specifications and generating procurement tables..."):
            try:
                # Configure AI
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # Extract text from PDF
                text = ""
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                
                if not text.strip():
                    st.error("Error: Could not extract text from the PDF. It might be scanned or image-based.")
                else:
                    # AI Prompt
                    prompt = """
                    You are an expert construction project engineer. Analyze the following project specification document.
                    Please structure the output vertically.
                    Do not use any Arabic text in the output. The output must be entirely in English.
                    
                    Task:
                    1. Identify all CSI MasterFormat Divisions present in the text.
                    2. Under each Division, list the corresponding Sections.
                    3. For each Section, generate a detailed Procurement Table containing these exact columns:
                       - Item Description
                       - Category (e.g., Bulk Material, Architectural, MEP Equipment)
                       - Lead Time & Risk Status (Use ⚠️ for Long-Lead items)
                       - Action Type (Classify as 'Essential' or 'Secondary / Minor')
                       
                    Format the entire response as clean Markdown. Use clear headers for Divisions and tables for the Sections.
                    
                    Specification Text:
                    """
                    
                    response = model.generate_content(prompt + text)
                    
                    st.success("Analysis Complete!")
                    st.markdown("### Analysis Output")
                    st.markdown(response.text)
                    
            except Exception as e:
                st.error(f"An error occurred during processing: {str(e)}")
