# AI CA Assistant for Indian SMEs


An AI-powered Chartered Accountant Assistant built with Streamlit and Google Gemini. This application allows Indian Small and Medium Enterprises (SMEs) to easily upload their transaction data or invoices and automatically generate GST returns (GSTR-1, GSTR-3B) while identifying potential errors and compliance issues.

## Features

- **File Processing:** Upload your CSV, JSON, PDF, XLSX, or TXT files to seamlessly extract transaction and invoice information.
- **GST Return Generation:** Automatically computes and generates the necessary structured JSON outputs for GSTR-1 and GSTR-3B.
- **Automated Compliance Checks:** Detects and flags errors in uploaded data with different severity levels (e.g., duplicate entries, missing GSTINs, anomalous tax rates).
- **Natural Language Interaction:** Ask questions or instruct the assistant to process data through an intuitive AI chat interface powered by Google Gemini.
- **Session-based Authentication:** Securely upload and process records within authenticated user sessions.


## Technologies Used
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Data Manipulation:** [Pandas](https://pandas.pydata.org/)
- **AI/LLM:** [Google Generative AI (Gemini)](https://ai.google.dev/)
- **PDF Extraction:** [pdfplumber](https://github.com/jsvine/pdfplumber)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chetan0321/ai-ca-assistant.git
   cd ai-ca-assistant
Create and activate a virtual environment:

# Windows
python -m venv .venv
.\.venv\Scripts\activate
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
Install the dependencies:

pip install -r requirements.txt
Configure Environment Variables: Create a new file named .env in the project root directory and add your Google Gemini API key:
GEMINI_API_KEY="your_actual_api_key_here"


# Project Structure
app.py: The entry point for the Streamlit GUI, handling routing, auth, chat interface, and result rendering.
file_parser.py: Responsible for extracting structural transaction data from different file formats (PDFs, CSVs, etc.).
gst_engine.py: Core logic for grouping transactions, computing returns based on GST laws, and identifying compliance errors.

