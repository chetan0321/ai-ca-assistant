import pandas as pd
import json
import pdfplumber
import streamlit as st
import google.generativeai as genai

def parse_csv_excel(file, file_type):
    if file_type in ["csv", "txt"]:
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
        
    # Standardize column names (lowercase, replace spaces with underscores)
    df.columns = [str(c).lower().replace(" ", "_").strip() for c in df.columns]
    
    transactions = []
    for _, row in df.iterrows():
        # Handle different column namings for user fallback
        tax_rate_raw = row.get("tax_rate", row.get("gst_rate", 0))
        # Strip '%' if it's a string
        if isinstance(tax_rate_raw, str):
            tax_rate_raw = tax_rate_raw.replace("%", "").strip()
        try:
            tax_rate = float(tax_rate_raw)
        except ValueError:
            tax_rate = 0.0

        trans = {
            "invoice_number": str(row.get("invoice_number", "")),
            "date": str(row.get("date", "")),
            "taxable_value": float(row.get("taxable_value", 0)),
            "tax_rate": tax_rate,
            "cgst": float(row.get("cgst", 0)),
            "sgst": float(row.get("sgst", 0)),
            "igst": float(row.get("igst", 0)),
            "party_gstin": str(row.get("party_gstin", row.get("customer_gstin", ""))),
            "hsn": str(row.get("hsn", "")),
            "place_of_supply": str(row.get("place_of_supply", row.get("state_code", ""))),
        }
        transactions.append(trans)
    return transactions

def parse_json(file):
    data = json.load(file)
    if isinstance(data, list):
        return data
    elif "invoices" in data:
        return data["invoices"]
    else:
        return []

def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

def parse_pdf_with_llm(file):
    text = extract_text_from_pdf(file)
    prompt = f"""
You are an AI assistant that extracts GST invoice details from text. 
Given the following invoice text, output a JSON array of transactions. 
Each transaction should have fields: invoice_number, date, taxable_value, tax_rate, cgst, sgst, igst, party_gstin, hsn, place_of_supply.
If any field is missing, use empty string or 0.

Invoice text:
{text}

Output only the JSON array. Do not wrap in markdown blocks like ```json.
"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    try:
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        transactions = json.loads(clean_text)
        return transactions
    except Exception as e:
        st.error(f"Failed to parse PDF with LLM. Error: {e} | Raw response: {response.text}")
        return []

def parse_file(file):
    file_type = file.name.split(".")[-1].lower()
    if file_type in ["csv", "txt"]:
        return parse_csv_excel(file, file_type)
    elif file_type in ["xls", "xlsx"]:
        return parse_csv_excel(file, "xlsx")
    elif file_type == "json":
        return parse_json(file)
    elif file_type == "pdf":
        return parse_pdf_with_llm(file)
    else:
        st.error(f"Unsupported file type: {file_type}")
        return []
