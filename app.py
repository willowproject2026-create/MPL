import os
import re
from pypdf import PdfReader
import google.generativeai as genai
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="PE Procurement Extractor",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Project Engineer - Automated Procurement Extractor")
st.markdown("Upload your CSI Specification PDF to automatically extract structured procurement logs organized and sorted by Divisions.")

# Secure API Key handling
api_key = None
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    pass

with st.sidebar:
    st.header("Configuration")
    if not api_key:
        api_key = st.text_input("Enter Gemini API Key", type="password")
    else:
        st.success("API Key loaded securely!")
    st.markdown("---")
    st.markdown("**Instructions:**")
    st.markdown("1. Upload the CSI specification PDF.")
    st.markdown("2. Click 'Run Analysis'.")

uploaded_file = st.file_uploader("Upload CSI Specification PDF", type=["pdf"])

def analyze_with_killer_prompt(model, division_name, text_content):
    killer_prompt = f"""
    You are an elite, senior Construction Project Engineer (PE) in the United States under CSI MasterFormat standards. 
    Analyze the provided specification text for {division_name} and extract a comprehensive, structured Procurement & Long-Lead Master Log. 

    Strict Rules for Output:
    1. Do not use any Arabic text. The output must be entirely in professional English.
    2. Structure the output as a clean Markdown table with the following exact columns:
       - CSI Division & Section
       - Item Description (Specific material, equipment, or product)
       - Supply Type (Contractor-Furnished vs. Owner-Furnished [OFCI / OFOI])
       - Estimated Lead Time / Risk Level (Standard, Long-Lead [⚠️ CRITICAL], or High-Risk)
       - Required Submittal Type (Shop Drawings, Product Data, Samples, or Attic Stock)
    3. Focus strictly on facts mentioned in the text. Do not hallucinate.

    Specification Text:
    {text_content[:30000]}
    """
    try:
        response = model.generate_content(killer_prompt)
        return response.text
    except Exception as e:
        return f"Error processing section: {str(e)}"

if uploaded_file is not None and api_key:
    if st.button("🚀 Run Hierarchical Analysis", type="primary"):
        # Fixed initialization using standard stable model name
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.status("Processing PDF and organizing divisions...", expanded=True) as status:
            temp_pdf_path = "temp_specs.pdf"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            reader = PdfReader(temp_pdf_path)
            total_pages = len(reader.pages)
            st.write(f"Total pages detected: {total_pages}. Scanning divisions...")
            
            section_pattern = re.compile(r'(\d{2})\s*(\d{2})\s*(\d{2})', re.IGNORECASE)
            
            hierarchy = {}
            current_division = "Division 00 - General Requirements"
            division_texts = {}
            
            for page_num in range(total_pages):
                text = reader.pages[page_num].extract_text()
                if not text:
                    continue
                    
                matches = section_pattern.search(text)
                if matches:
                    div_num = matches.group(1)
                    current_division = f"Division {div_num}"
                
                if current_division not in division_texts:
                    division_texts[current_division] = ""
                division_texts[current_division] += text + "\n"
                
            extracted_results = {}
            # Process and analyze each division text chunk
            for div_name, div_content in division_texts.items():
                extracted_results[div_name] = analyze_with_killer_prompt(model, div_name, div_content[:25000])
                
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                
            status.update(label="Analysis complete!", state="complete", expanded=False)
        
        st.success("Divisions successfully sorted and analyzed!")
        
        # Sort divisions numerically/alphabetically so they appear in correct order
        sorted_divisions = sorted(extracted_results.keys())
        
        for division_name in sorted_divisions:
            analysis = extracted_results[division_name]
            with st.expander(f"📁 {division_name}"):
                st.markdown(analysis)

elif uploaded_file and not api_key:
    st.warning("⚠️ Please provide your Gemini API key.")
