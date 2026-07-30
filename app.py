import os
import re
from pypdf import PdfReader
import google.generativeai as genai

def run_pe_procurement_extractor(pdf_path, gemini_api_key):
    # 1. Configure Gemini
    genai.configure(api_key=gemini_api_key)
    # Using a fast, high-context model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"[*] Total pages detected: {total_pages}. Scanning for CSI Sections...")
    
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
            # If we were processing an existing section, run the AI Killer Prompt on it before moving on
            if section_text.strip():
                print(f"[*] Processing {current_section} via AI Killer Prompt...")
                extracted_results[current_section] = analyze_with_killer_prompt(model, current_section, section_text)
            
            current_section = f"Section_{matches[0].replace(' ', '_')}"
            section_text = ""
            
        section_text += text + "\n"
        
    # Process the last section
    if section_text.strip():
        print(f"[*] Processing final section {current_section} via AI Killer Prompt...")
        extracted_results[current_section] = analyze_with_killer_prompt(model, current_section, section_text)
        
    print("[+] Processing complete! All sections extracted and analyzed successfully.")
    return extracted_results

def analyze_with_killer_prompt(model, section_name, text_content):
    # The Elite PE AI Killer Prompt
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
    {text_content[:30000]}  # Safely capping chunk size to maintain absolute precision
    """
    
    try:
        response = model.generate_content(killer_prompt)
        return response.text
    except Exception as e:
        return f"Error processing section: {str(e)}"

# طريقة التشغيل:
# results = run_pe_procurement_extractor("path_to_large_specs.pdf", "YOUR_GEMINI_API_KEY")
# for sec, analysis in results.items():
#     print(f"\n--- {sec} ---\n")
#     print(analysis)
