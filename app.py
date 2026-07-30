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
st.markdown("Upload your CSI Specification PDF to extract structured procurement logs organized strictly by valid MasterFormat Divisions.")

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
        # Using the standard generative model call
        response = model.generate_content(killer_prompt)
        return response.text
    except Exception as e:
        return f"Error processing section: {str(e)}"

if uploaded_file is not None and api_key:
    if st.button("🚀 Run Clean Hierarchical Analysis", type="primary"):
        # Configure using the correct client initialization
        genai.configure(api_key=api_key)
        
        # Explicitly use the stable gemini-1.5-flash model name supported by the API
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        with st.status("Processing PDF and filtering valid divisions...", expanded=True) as status:
            temp_pdf_path = "temp_specs.pdf"
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            reader = PdfReader(temp_pdf_path)
            total_pages = len(reader.pages)
            st.write(f"Total pages detected: {total_pages}. Parsing valid CSI Divisions...")
            
            # Strict regex to capture valid 2-digit CSI MasterFormat Divisions (00 through 48)
            division_pattern = re.compile(r'\b(0[0-9]|1[0-4]|2[1-8]|3[1-5]|4[0-8])\s*00\s*00\b|\b(0[0-9]|1[0-4]|2[1-8]|3[1-5]|4[0-8])\b', re.IGNORECASE)
            
            division_texts = {}
            current_division = "Division 01 - General Requirements"
            division_texts[current_division] = ""
            
            for page_num in range(total_pages):
                text = reader.pages[page_num].extract_text()
                if not text:
                    continue
                    
                # Look for clear division headers in the page text
                matches = division_pattern.findall(text)
                if matches:
                    for match in matches:
                        div_num = match[0] or match[1]
                        if div_num:
                            potential_div = f"Division {div_num}"
                            if potential_div != current_division:
                                current_division = potential_div
                                if current_division not in division_texts:
                                    division_texts[current_division] = ""
                
                division_texts[current_division] += text + "\n"
                
            extracted_results = {}
            # Filter out empty or invalid noise entries, process only legitimate divisions with content
            for div_name, div_content in division_texts.items():
                if len(div_content.strip()) > 500: # Ensure there's actual content to analyze
                    extracted_results[div_name] = analyze_with_killer_prompt(model, div_name, div_content[:25000])
                
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                
            status.update(label="Analysis complete successfully!", state="complete", expanded=False)
        
        if extracted_results:
            st.success("Valid divisions successfully parsed and analyzed!")
            # Sort divisions numerically so they appear in correct order (Division 01, 02, 08, etc.)
            sorted_divisions = sorted(extracted_results.keys())
            
            for division_name in sorted_divisions:
                analysis = extracted_results[division_name]
                with st.expander(f"📁 {division_name}"):
                    st.markdown(analysis)
        else:
            st.warning("⚠️ No valid CSI divisions were detected with sufficient text. Please check the PDF format.")

elif uploaded_file and not api_key:
    st.warning("⚠️ Please provide your Gemini API key.")
