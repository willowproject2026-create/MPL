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
st.markdown("Upload your CSI Specification PDF to automatically extract structured procurement, long-lead, and submittal logs per section.")

# Sidebar for API Configuration
with st.sidebar:
    st.header("Configuration")
    api_key_input = st.text_input("Enter Gemini API Key", type="password")
    st.markdown("---")
    st.markdown("**Instructions:**")
    st.markdown("1. Enter your Gemini API key.")
    st.markdown("2. Upload the CSI specification PDF.")
    st.markdown("3. Click 'Run Analysis' to process sections automatically.")

# Main File Uploader
uploaded_file = st.file_uploader("Upload CSI Specification PDF", type=["pdf"])

def analyze_with_killer_prompt(model, section_name, text_content):
    killer_prompt = f"""
    You are an elite, senior Construction Project Engineer (PE) in the United States under CSI MasterFormat standards. 
    Analyze the provided specification text for {section_name} and extract a comprehensive, structured Procurement & Long-Lead Master Log. 

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

if uploaded_file is not None and api_key_input:
    if st.button("🚀 Run Procurement Analysis", type="primary"):
        genai.configure(api_key=api_key_input)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.status("Processing PDF and extracting sections...", expanded=True) as status:
            # Save uploaded file temporarily
            temp_pdf_path = "temp_specs.pdf"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            reader = PdfReader(temp_pdf_path)
            total_pages = len(reader.pages)
            st.write(f"Total pages detected: {total_pages}. Scanning for CSI Sections...")
            
            section_pattern = re.compile(r'(?:Section\s*)?(\d{2}\s*\d{2}\s*\d{2})', re.IGNORECASE)
            
            current_section = "General_Introduction"
            section_text = ""
            extracted_results = {}

            for page_num in range(total_pages):
                text = reader.pages[page_num].extract_text()
                if not text:
                    continue
                    
                matches = section_pattern.findall(text)
                if matches:
                    if section_text.strip():
                        extracted_results[current_section] = analyze_with_killer_prompt(model, current_section, section_text)
                    
                    current_section = f"Section_{matches[0].replace(' ', '_')}"
                    section_text = ""
                    
                section_text += text + "\n"
                
            if section_text.strip():
                extracted_results[current_section] = analyze_with_killer_prompt(model, current_section, section_text)
                
            # Clean up temp file
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                
            status.update(label="Analysis complete successfully!", state="complete", expanded=False)
        
        st.success("All sections have been successfully parsed and analyzed!")
        
        # Display Results in Tabs or Expanders
        for sec, analysis in extracted_results.items():
            with st.expander(f"📌 {sec.replace('_', ' ')}"):
                st.markdown(analysis)

elif uploaded_file and not api_key_input:
    st.warning("⚠️ Please enter your Gemini API key in the sidebar to proceed.")
