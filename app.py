import streamlit as st
import pandas as pd
import pdfplumber
import json
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

import file_parser
import gst_engine

load_dotenv()
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    st.warning("Could not initially configure Gemini API. Ensure API key is correct.")

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None

# Login page
def login():
    st.title("AI CA Assistant - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # For demo, accept any non-empty username/password
        if username and password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid credentials")

# Logout function
def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.rerun()

# Main app after login
def main():
    st.set_page_config(page_title="AI CA Assistant", page_icon="🤖")
    st.sidebar.button("Logout", on_click=logout)
    st.sidebar.write(f"Logged in as: {st.session_state.username}")

    st.title("AI CA Assistant for Indian SMEs")
    st.markdown("Upload your invoices/transaction files (CSV, JSON, PDF) and get GST returns and error reports.")

    # Chat input area
    user_input = st.chat_input("Ask me to process your data or upload a file...")
    if user_input:
        # Process as a message
        st.session_state.chat_history.append(("user", user_input))
        response = handle_message(user_input)
        st.session_state.chat_history.append(("assistant", response))
    
    # Display chat history
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(text)
    
    # File uploader (appears below chat)
    uploaded_file = st.file_uploader("Upload file", type=["csv", "json", "pdf", "xlsx", "txt"])
    if uploaded_file is not None:
        process_file(uploaded_file)
        
    display_results()

def handle_message(msg):
    # Placeholder for natural language processing
    return f"I received your message: '{msg}'. You can upload a file (CSV, JSON, PDF) and I'll process it for GST."

def process_file(file):
    st.info(f"Extracting data from {file.name}...")
    transactions = file_parser.parse_file(file)
    
    if not transactions:
        st.error("No transactions extracted or failed to parse.")
        return

    # In a full app, user_state would be part of a settings page. We'll default to "07" (Delhi).
    user_state = "07"
    
    gstr1 = gst_engine.generate_gstr1(transactions, user_state=user_state)
    gstr3b = gst_engine.generate_gstr3b(transactions)
    errors = gst_engine.detect_errors(transactions)

    st.session_state.processed_data = {
        "gstr1": gstr1,
        "gstr3b": gstr3b,
        "errors": errors,
        "transactions": transactions
    }
    st.success("File processed successfully! View results below.")

def display_results():
    if st.session_state.processed_data:
        data = st.session_state.processed_data
        
        st.subheader("1. Extracted Data")
        with st.expander("View Raw Transactions", expanded=False):
            st.dataframe(data["transactions"])

        st.subheader("2. GST Returns")
        col1, col2 = st.columns(2)
        
        gstr1_json = json.dumps(data["gstr1"], indent=2)
        with col1:
             st.download_button(
                 label="⬇️ Download GSTR-1 JSON",
                 data=gstr1_json,
                 file_name=f"gstr1_{datetime.now().strftime('%Y%m%d')}.json",
                 mime="application/json",
                 use_container_width=True
             )
             
        gstr3b_json = json.dumps(data["gstr3b"], indent=2)
        with col2:
             st.download_button(
                 label="⬇️ Download GSTR-3B JSON",
                 data=gstr3b_json,
                 file_name=f"gstr3b_{datetime.now().strftime('%Y%m%d')}.json",
                 mime="application/json",
                 use_container_width=True
             )

        st.subheader("3. Compliance Checks")
        if data["errors"]:
            st.error(f"⚠️ {len(data['errors'])} Issues Found in the uploaded data!")
            for e in data["errors"]:
                if e['severity'] == 'high':
                     st.error(f"❌ **HIGH**: {e['error']} (Row #{e['transaction_index']})")
                else:
                     st.warning(f"⚠️ **{e['severity'].upper()}**: {e['error']} (Row #{e['transaction_index']})")
        else:
            st.success("✅ No errors found! Your data looks clean.")

# Entry point
if st.session_state.authenticated:
    main()
else:
    login()
