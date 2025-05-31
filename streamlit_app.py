import streamlit as st
import os
import base64
import requests
from dotenv import load_dotenv
import openai
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
import time,datetime
import json
import asyncio # Import asyncio for asynchronous tasks
import httpx # Import httpx for asynchronous HTTP requests
import pandas as pd 
# Load API key
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = openai_api_key

# Initialize LangChain model + JSON parser
model = ChatOpenAI(model='gpt-4o-mini', temperature=0.0)
chain = model | JsonOutputParser()

# Ensure upload directories exist
UPLOAD_DIR = "emirates_id"
BANK_DIR = "bank-statements"
CREDIT_DIR = "credit_reports"
RESUME_DIR = "resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BANK_DIR, exist_ok=True)
os.makedirs(CREDIT_DIR, exist_ok=True)
os.makedirs(RESUME_DIR, exist_ok=True)

async def call_submit_api_async(emirates_id: str, evaluation_result: dict):
    """
    Asynchronously calls the /submit endpoint.
    """
    payload = {
        "emirates_id": emirates_id,
        "evaluation_result": evaluation_result # This is now the final evaluation result
    }
    submit_url = "http://localhost:5050/submit"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(submit_url, json=payload)
            # You might want to log the response or handle specific status codes here
            # For a fire-and-forget, we might not need to do much with the response
            if response.status_code == 200:
                print(f"Successfully submitted data for EID {emirates_id} to {submit_url}") # Server-side log
            else:
                print(f"Failed to submit data for EID {emirates_id} to {submit_url}. Status: {response.status_code}, Response: {response.text}") # Server-side log
    except httpx.RequestError as e:
        print(f"An error occurred while calling {submit_url}: {e}") # Server-side log
    except Exception as e:
        print(f"An unexpected error occurred in call_submit_api_async: {e}") # Server-side log


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def display_extracted(data: dict):
    st.markdown("### Extracted Emirates ID Details")
    for key, value in data.items():
        st.markdown(f"**{key.replace('_',' ').title()}:** {value}")

def display_evaluation_result(result: dict, app_type: str):
    st.markdown(f"### {app_type} Evaluation Result")
    
    if "error" in result:
        st.error(f"**Error during evaluation:** {result['error']}")
        return

    actual_result = result 

    def _parse_stringified_json_value(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass 
        return None

    parsed_nested_result = None

    if "result" in actual_result:
        parsed_nested_result = _parse_stringified_json_value(actual_result["result"])
        if parsed_nested_result is not None:
            actual_result = parsed_nested_result
        elif isinstance(actual_result["result"], dict):
            actual_result = actual_result["result"]
            
    if parsed_nested_result is None and "Result" in actual_result:
        parsed_nested_result = _parse_stringified_json_value(actual_result["Result"])
        if parsed_nested_result is not None:
            actual_result = parsed_nested_result

    status_key = None
    if app_type == "Social Economic Support":
        status_key = "financial_support_decision"
    elif app_type == "Social Economic Enablement":
        status_key = "enablement_decision" 

    status = actual_result.get(status_key)
    if status:
        if status.lower() == "approved":
            st.success(f"**Application Status:** {status.replace('_',' ').title()} 🎉")
        elif status.lower() == "rejected" or status.lower() == "soft decline":
            st.error(f"**Application Status:** {status.replace('_',' ').title()} 😔")
        else:
            st.info(f"**Application Status:** {status.replace('_',' ').title()}")
    else:
        st.warning("Application Status: Not Available")

    reason = actual_result.get("reason")
    if reason:
        st.markdown(f"**Reason:** {reason}")

    if app_type == "Social Economic Support":
        financial_assessment = actual_result.get("financial_assessment")
        if financial_assessment and isinstance(financial_assessment, dict):
            st.markdown("---")
            st.markdown("#### Financial Assessment")
            for key, value in financial_assessment.items():
                st.markdown(f"**{key.replace('_',' ').title()}:** {value}")
        
    elif app_type == "Social Economic Enablement":
        career_assessment = actual_result.get("career_assessment")
        # There was a bug here: for key, value in career_assessment.items(): you used sub_key, sub_value
        if career_assessment and isinstance(career_assessment, dict):
            st.markdown("---")
            st.markdown("#### Career Assessment")
            for key, value in career_assessment.items(): # Corrected this line
                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{key.replace('_',' ').title()}:** {value}") # Corrected this line
        
        st.markdown("---")
        st.markdown("#### Full Evaluation Details:")
        for key, value in actual_result.items():
            if key not in [status_key, "reason", "financial_assessment", "career_assessment", "recommendation", "error"]:
                if isinstance(value, dict):
                    st.markdown(f"**{key.replace('_',' ').title()}:**")
                    for sub_key, sub_value in value.items():
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;**{sub_key.replace('_',' ').title()}:** {sub_value}")
                else:
                    st.markdown(f"**{key.replace('_',' ').title()}:** {value}")

    recommendation = actual_result.get("recommendation")
    if recommendation:
        st.markdown("---")
        st.markdown("#### Recommendation")
        st.markdown(f"{recommendation}")

def main():
    st.set_page_config(page_title="Social Support Application Portal", layout="centered", page_icon="🏛️")

    # CSS (minimized for brevity in this response, but it's the same as your provided file)
    st.markdown(
        """
        <style>
        /* ... Your existing CSS ... */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

        html, body, [class*="st-emotion-cache"] {
            font-family: 'Poppins', sans-serif;
            color: #333333;
            line-height: 1.7;
        }

        .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important; 
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .main-header {
            font-size: 2.8em;
            color: #1a7a49;
            text-align: center;
            margin-bottom: 15px; 
            font-weight: 700;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
            margin-top: 15px; 
        }
        .subheader {
            font-size: 1.3em;
            color: #555555;
            text-align: center;
            margin-bottom: 20px; 
            line-height: 1.6;
        }
        .portal-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0px; 
            border-radius: 15px;
            background-color: #ffffff;
            box-shadow: 0 0px 0px rgba(0, 0, 0, 0.0); 
            margin-top: 0px; 
            margin-bottom: 0px; 
            border: none; 
        }
        .stButton button {
            background-color: #28a745;
            color: white;
            padding: 16px 35px;
            border-radius: 8px;
            border: none;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
            box-shadow: 0 4px 10px rgba(40, 167, 69, 0.2);
            margin: 15px 0; 
        }
        .stButton button:hover {
            background-color: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(40, 167, 69, 0.3);
        }
        .stButton button:active {
            transform: translateY(0);
            box-shadow: 0 2px 5px rgba(40, 167, 69, 0.2);
        }

        .stButton button[key="back_button_general"],
        .stButton button[key*="_back"],
        .stButton button[key="home_button_sidebar"] {
            background-color: #6c757d;
            box-shadow: 0 2px 8px rgba(108, 117, 125, 0.2);
        }
        .stButton button[key="back_button_general"]:hover,
        .stButton button[key*="_back"]:hover,
        .stButton button[key="home_button_sidebar"]:hover {
            background-color: #5a6268;
            box_shadow: 0 4px 12px rgba(108, 117, 125, 0.3);
        }

        .stButton button[key*="switch_to_"] {
            background-color: #17a2b8;
            box-shadow: 0 2px 8px rgba(23, 162, 184, 0.2);
        }
        .stButton button[key*="switch_to_"]:hover {
            background-color: #138496;
            box-shadow: 0 4px 12px rgba(23, 162, 184, 0.3);
        }

        .info-section-title {
            font-size: 1.8em;
            color: #333333;
            text-align: center;
            margin-top: 30px; 
            margin-bottom: 15px; 
            font-weight: 600;
        }
        .info-list {
            list-style-type: none;
            padding: 0;
            text-align: left;
            width: 90%;
            max-width: 700px;
            margin: 0 auto 20px auto; 
        }
        .info-list li {
            background: #f8f9fa;
            margin: 10px 0; 
            padding: 15px 20px; 
            border-radius: 10px;
            display: flex;
            align-items: flex-start;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #28a745;
        }
        .info-list li::before {
            content: '✓';
            font-size: 1.2em;
            font-weight: bold;
            color: #28a745;
            margin-right: 15px;
            line-height: 1.7;
        }
        .info-list li ul {
            margin-top: 5px; 
            padding-left: 20px; 
            list-style-type: disc;
        }
        .info-list li ul li {
            background: none;
            box-shadow: none;
            border-left: none;
            padding: 3px 0; 
            margin: 0;
        }
        .info-list li ul li::before {
            content: '';
            margin-right: 0;
        }


        .footer-note {
            font-size: 0.95em;
            color: #666666;
            text-align: center;
            margin-top: 25px; 
            padding: 15px; 
            background-color: #e9ecef;
            border-radius: 10px;
            border: 1px solid #dee2e6;
        }
        .sidebar .sidebar-content {
            background-color: #e9f5ee;
            border-right: 1px solid #d4edda;
            box-shadow: 2px 0 10px rgba(0,0,0,0.05);
            padding-top: 2rem;
        }
        [data-testid="stSidebarContent"] h1 {
            padding-top: 2rem;
            padding-bottom: 1rem;
            font-size: 1.8em;
            color: #1a7a49;
            font-weight: 700;
        }
        [data-testid="stSidebarNav"] li > a {
            font-size: 1.1em;
            padding: 10px 20px;
            margin-bottom: 8px;
            border-radius: 5px;
            transition: background-color 0.3s, color 0.3s;
        }
        [data-testid="stSidebarNav"] li > a:hover {
            background-color: #d4edda;
            color: #1a7a49;
        }
        [data-testid="stSidebarNav"] li > a[data-active="true"] {
            background-color: #28a745;
            color: white;
            font-weight: 600;
        }

        div[data-testid="stForm"] {
            padding: 20px; 
            border-radius: 12px;
            background-color: #fcfcfc;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e0e0e0;
            margin-top: 20px; 
            margin-bottom: 20px; 
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stNumberInput"] label,
        div[data-testid="stDateInput"] label,
        div[data-testid="stSelectbox"] label,
        div[data-testid="stFileUploader"] label,
        div[data-testid="stRadio"] > label { /* This was stRadio > label, but Streamlit structure might be div > div for radio options */
            margin-bottom: 5px; 
            font-weight: 500;
            color: #333333;
            display: block;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input {
            border: 1px solid #cccccc;
            border-radius: 8px;
            padding: 8px 12px; 
            font-size: 1.0em; 
            transition: border-color 0.3s, box-shadow 0.3s;
            background-color: #ffffff;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
            margin-bottom: 15px; 
            width: 100%;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stDateInput"] input:focus {
            border-color: #28a745;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
            outline: none;
        }

        div[data-testid="stSelectbox"] > div[role="button"] {
            border: 1px solid #cccccc;
            border-radius: 8px;
            padding: 8px 12px; 
            font-size: 1.0em; 
            background-color: #ffffff;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
            transition: border-color 0.3s, box-shadow 0.3s;
            margin-bottom: 15px; 
            width: 100%;
        }
        div[data-testid="stSelectbox"] > div[role="button"]:focus {
            border-color: #28a745;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25);
            outline: none;
        }

        div[data-testid="stFileUploader"] section {
            border: 2px dashed #a0d3a0;
            border-radius: 8px;
            padding: 15px; 
            background-color: #f7fff7;
            text-align: center;
            transition: border-color 0.3s ease, background-color 0.3s ease;
            margin-bottom: 20px; 
        }
        div[data-testid="stFileUploader"] section:hover {
            border-color: #28a745;
            background-color: #e6ffe6;
        }
        div[data-testid="stFileUploader"] button {
            background-color: #28a745 !important;
            color: white !important;
            border: none !important;
        }
        div[data-testid="stFileUploader"] button:hover {
            background-color: #218838 !important;
        }

        div[data-testid="stRadio"] label[data-testid^="stRadioLabel"] {
            background-color: #f0f0f0;
            padding: 8px 12px; 
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
            cursor: pointer;
            flex-grow: 1;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin: 0; 
        }
        div[data-testid="stRadio"] label[data-testid^="stRadioLabel"]:hover {
            background-color: #e5e5e5;
            border-color: #c0c0c0;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        div[data-testid="stRadio"] input[type="radio"] {
            display: none; /* Hide the actual radio button */
        }
        /* Style the label when the radio is checked */
        div[data-testid="stRadio"] input[type="radio"]:checked + label[data-testid^="stRadioLabel"] {
            background-color: #28a745; /* Green background for selected */
            color: white;
            border-color: #28a745;
            box-shadow: 0 4px 10px rgba(40, 167, 69, 0.2);
        }

        /* Container for radio buttons */
        div[data-testid="stRadio"] {
            display: flex;
            gap: 10px; 
            flex-wrap: wrap;
            margin-bottom: 20px; 
            width: 100%;
        }
        /* Streamlit wraps each radio option in a div, target that for layout if needed */
        div[data-testid="stRadio"] > div[data-testid^="stFlex"] { 
            margin: 0; /* Remove default margins if Streamlit adds them here */
            padding: 0;
        }


        .stSpinner > div > div {
            border-top-color: #28a745;
        }
        .stSpinner {
            color: #555555;
            font-size: 1.1em;
            font-weight: 500;
            margin-top: 15px; 
            margin-bottom: 15px; 
        }
        .stSuccess {
            background-color: #d4edda;
            color: #155724;
            border-radius: 8px;
            padding: 12px 15px; 
            border: 1px solid #c3e6cb;
            margin-top: 15px; 
            margin-bottom: 15px; 
        }
        .stError {
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 8px;
            padding: 12px 15px; 
            border: 1px solid #f5c6cb;
            margin-top: 15px; 
            margin-bottom: 15px; 
        }
        .stWarning {
            background-color: #fff3cd;
            color: #856404;
            border-radius: 8px;
            padding: 12px 15px; 
            border: 1px solid #ffeeba;
            margin-top: 15px; 
            margin-bottom: 15px; 
        }

        /* General heading styles */
        h1, h2, h3, h4, h5, h6 {
            color: #1a7a49;
            font-weight: 600;
            margin-top: 1.5em; 
            margin-bottom: 0.8em; 
            padding-bottom: 5px; /* Add some space below the border */
            border-bottom: 1px solid #f0f0f0; /* Light border for separation */
        }
        h1 { font-size: 2.0em; } 
        h2 { font-size: 1.7em; } 
        h3 { font-size: 1.4em; } 

        </style>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.title("Navigation")
    
    if st.sidebar.button("🏠 Home", key="home_button_sidebar"): # Using a distinct key
        # Clear relevant session state variables when going home
        keys_to_clear = [
            "step", "choice", "extracted", "filename", "id_image_path", "emirates_id",
            "applicant_data", "evaluation_in_progress", "evaluation_done", 
            "evaluation_result", "bank_statement_path", "credit_report_path", 
            "resume_filename", "resume_path", "enablement_evaluation_done"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.step = 0 # Explicitly set step to 0 AFTER clearing
        st.experimental_rerun()
    
    st.sidebar.markdown("---")

    # Updated Navigation Logic
    nav_config = [
        ("Welcome", [0]),
        ("Emirates ID", [1]),
        ("Review Info", [2]),
        ("Application Path", [3]),
        ("Personal Info", [4, 6]), # Step 4 for Support, Step 6 for Enablement
        ("Upload Docs & Evaluate", [5, 7]) # Step 5 for Support, Step 7 for Enablement
    ]
    current_s_step = st.session_state.get("step", 0)

    for idx, (label, item_steps) in enumerate(nav_config):
        is_active = current_s_step in item_steps
        
        is_completed = False
        if not is_active:
            # A nav item is completed if all its associated steps are numerically less than the current step
            if all(s < current_s_step for s in item_steps):
                is_completed = True
        
        # Ensure Welcome (step 0) is correctly marked active initially and not completed
        if idx == 0 and current_s_step == 0:
            is_active = True
            is_completed = False

        # Using st.page_link for navigation (requires Streamlit 1.34+)
        # For this example, sticking to CSS-styled markdown for compatibility with original code structure
        # but st.page_link would be the modern way if pages were separate .py files.
        # The class "st-emotion-cache-10q273q" is an internal Streamlit class.
        # It's better to define your own if possible for long-term stability.
        nav_item_html_class = "st-emotion-cache-10q273q" # From original user code

        if is_completed:
            st.sidebar.markdown(f'<div class="{nav_item_html_class}" data-active="false">✅ {label}</div>', unsafe_allow_html=True)
        elif is_active:
            st.sidebar.markdown(f'<div class="{nav_item_html_class}" data-active="true">🔷 {label}</div>', unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f'<div class="{nav_item_html_class}">▫️ {label}</div>', unsafe_allow_html=True)


    if "step" not in st.session_state:
        st.session_state.step = 0

    # Back button logic (simplified from previous complex version, assuming simple step back)
    if st.session_state.step > 0:
        if st.button("← Back", key="back_button_general"):
            # Simple step back. More complex logic can be added if needed based on current_s_step.
            # For example, from step 4 (Support Personal Info) or 6 (Enablement Personal Info) go to 3.
            if current_s_step in [4, 6]:
                st.session_state.step = 3
            elif current_s_step == 5 : # Support Docs -> Support Personal
                st.session_state.step = 4
            elif current_s_step == 7 : # Enablement Eval -> Enablement Personal
                st.session_state.step = 6
            else:
                st.session_state.step -=1
            
            # Reset evaluation flags if going back from an evaluation step or to a form step
            if "evaluation_in_progress" in st.session_state: del st.session_state.evaluation_in_progress
            if "evaluation_done" in st.session_state: del st.session_state.evaluation_done
            if "enablement_evaluation_done" in st.session_state: del st.session_state.enablement_evaluation_done

            st.experimental_rerun()
        st.markdown("---")

    # --- Page Content ---
    if st.session_state.step == 0:
        st.markdown('<div class="portal-container">', unsafe_allow_html=True)
        st.markdown('<div class="main-header">🏛️ Welcome to the Social Support Application Portal</div>', unsafe_allow_html=True)
        st.markdown('<div class="subheader">This portal is designed to help you apply for financial assistance or career enablement support based on your current circumstances.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="info-section-title">What to Expect:</div>', unsafe_allow_html=True)
        st.markdown("""
            <ul class="info-list">
                <li>Upload your Emirates ID for automatic verification.</li>
                <li>Choose the application path that suits your needs:
                    <ul>
                        <li><b>Economic Support</b> if you're seeking financial aid.</li>
                        <li><b>Enablement Support</b> if you're looking to improve your employment situation.</li>
                    </ul>
                </li>
                <li>Submit required documents such as bank statements and credit reports.</li>
                <li>Our intelligent evaluation system will assess your eligibility securely and transparently.</li>
            </ul>
        """, unsafe_allow_html=True)

        st.markdown('<div class="footer-note">🔒 Your data is confidential and used solely for eligibility evaluation.</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; margin-top: 20px;">', unsafe_allow_html=True)
        if st.button("Click Start to begin your application.", key="start_application"):
            st.session_state.step = 1
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.step == 1:
        st.header("Step 1: Upload Your Emirates ID") # Changed to header
        st.write("Please upload a clear photo of your Emirates ID in **JPEG** or **PNG** format.")
        st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True) # More pronounced separator

        # Using st.form for better layout and submission handling for this specific step
        with st.form("emirates_id_upload_form", clear_on_submit=True): # Clear form on successful submit
            uploaded_file = st.file_uploader("Choose Emirates ID image:", type=["jpg", "jpeg", "png"], label_visibility="visible")
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True) # Spacing
            confirmation_checkbox = st.checkbox("I confirm this is my genuine Emirates ID and not a counterfeit document.")
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
            submit_button = st.form_submit_button("Submit and Extract Details")

        if submit_button:
            if not uploaded_file:
                st.error("No file selected. Please upload an image of your Emirates ID.")
            elif not confirmation_checkbox:
                st.error("Please confirm the authenticity of your Emirates ID before proceeding.")
            else:
                with st.spinner("Processing your Emirates ID... This may take a moment."):
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    # Create a unique temporary filename to avoid conflicts
                    temp_filename = f"temp_eid_{time.time_ns()}.{file_extension}"
                    temp_file_path = os.path.join(UPLOAD_DIR, temp_filename)

                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    base64_image = encode_image(temp_file_path)
                    data_uri_image = f"data:image/{file_extension};base64,{base64_image}"
                    
                    extraction_prompt = """
                        Extract the full name, nationality, ID number (without masking any digits), gender (Male or Female),
                        and expiry date from the provided Emirates ID image.
                        The output must be a JSON object with the following keys:
                        "full_name", "id_number", "expiry_date", "gender", "nationality".
                        Example format for a successful extraction:
                        {
                            "full_name": "FIRSTNAME MIDDLENAME LASTNAME",
                            "id_number": "784-YYYY-XXXXXXX-X",
                            "expiry_date": "DD/MM/YYYY", 
                            "gender": "Male",
                            "nationality": "COUNTRY NAME"
                        }
                        If any field cannot be clearly extracted, use "Not Found" as its value.
                        Ensure the 'expiry_date' is in DD/MM/YYYY format.
                    """

                    llm_message = {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extraction_prompt},
                            {"type": "image_url", "image_url": {"url": data_uri_image}}
                        ],
                    }

                    try:
                        # --- LLM Call for Extraction ---
                        extracted_data_from_llm = chain.invoke([llm_message])
                        
                        # Ensure 'id_number' is present for filename and further use
                        emirates_id_number = extracted_data_from_llm.get("id_number", f"unknown_eid_{time.time_ns()}")
                        if emirates_id_number == "Not Found" or not emirates_id_number.strip():
                            emirates_id_number = f"eid_extraction_failed_{time.time_ns()}"
                            st.warning("Could not reliably extract the ID number. Please ensure the image is very clear.")

                        # Rename the uploaded file using the extracted (or generated) EID
                        # Sanitize EID for use in filename (replace common problematic chars)
                        sanitized_eid_for_filename = emirates_id_number.replace('-', '_').replace('/', '_').replace('\\', '_')
                        final_image_filename = f"{sanitized_eid_for_filename}.{file_extension}"
                        final_image_path = os.path.join(UPLOAD_DIR, final_image_filename)

                        # Handle potential file overwrite or use unique names if needed
                        if os.path.exists(final_image_path) and temp_file_path != final_image_path :
                            os.remove(final_image_path) # Remove old if it exists to replace with new scan
                        os.rename(temp_file_path, final_image_path)
                        
                        # Store extracted data and details in session state
                        st.session_state.extracted = extracted_data_from_llm
                        st.session_state.filename = final_image_filename
                        st.session_state.id_image_path = final_image_path
                        st.session_state.emirates_id = emirates_id_number # Use the potentially fallback EID

                        # --- <<<< ASYNCHRONOUS API CALL REMOVED FROM HERE >>>> ---
                        # It will now be called after the evaluation result is available

                        st.session_state.step = 2 # Move to the review step
                        st.experimental_rerun()

                    except Exception as e:
                        st.error(f"An error occurred during data extraction: {str(e)}. Please ensure the uploaded image is clear and valid.")
                        # Clean up the temporary file if it still exists after an error
                        if os.path.exists(temp_file_path):
                            try:
                                os.remove(temp_file_path)
                            except OSError as unlink_error:
                                st.warning(f"Could not remove temporary file: {unlink_error}")
                        # Do not proceed to the next step on error
    
    elif st.session_state.step == 2:
        st.header("Step 2: Review Extracted Information") # Changed to header
        st.write("Please carefully review the details extracted from your Emirates ID. If all information is correct, click 'Accept & Proceed'. If there are discrepancies, click 'Reject & Re-upload' to try again with a clearer image.")
        st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)


        if "filename" in st.session_state:
            st.markdown(f"**Uploaded File:** `{st.session_state.filename}` ✅")
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
        
        if "extracted" in st.session_state and st.session_state.extracted:
            display_extracted(st.session_state.extracted)
        else:
            st.warning("No information was extracted, or the extracted data is empty. Please go back and re-upload your ID.")
        
        st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        
        col1, col_spacer, col2 = st.columns([2, 0.1, 2]) # Use columns for button layout
        with col1:
            if st.button("✅ Accept & Proceed", key="accept_id_details", use_container_width=True):
                st.session_state.step = 3
                st.experimental_rerun()
        with col2:
            if st.button("❌ Reject & Re-upload", key="reject_id_details", type="secondary", use_container_width=True):
                # Clear previously extracted data to ensure a fresh start for re-upload
                keys_to_clear_on_reject = ["extracted", "filename", "id_image_path", "emirates_id"]
                for key_to_clear in keys_to_clear_on_reject:
                    if key_to_clear in st.session_state:
                        del st.session_state[key_to_clear]
                st.session_state.step = 1 # Go back to the upload step
                st.experimental_rerun()

    elif st.session_state.step == 3:
        st.header("Step 3: Choose Your Application Path") # Changed to header
        st.write("Select whether you are applying for financial aid (Economic Support) or assistance with employment (Enablement Support). Your choice will determine the subsequent steps and required information.")
        st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

        # Using columns for a side-by-side button layout
        col1, col_spacer, col2 = st.columns([2, 0.2, 2]) 
        
        with col1:
            if st.button("💰 Social Economic Support", key="select_support_path", use_container_width=True, help="Apply for financial assistance programs based on your economic situation."):
                st.session_state.choice = "support"
                st.session_state.step = 4 # Proceed to Support Path Personal Info
                st.experimental_rerun()
        
        with col2:
            if st.button("🛠️ Social Economic Enablement", key="select_enablement_path", use_container_width=True, help="Apply for career development, upskilling, and employment support programs."):
                st.session_state.choice = "enablement"
                st.session_state.step = 6 # Proceed to Enablement Path Personal Info
                st.experimental_rerun()
    
    # --- Step 4: Social Economic Support Form ---
    elif st.session_state.step == 4:
        st.header("Step 4: Applicant Information (Economic Support)")
        st.write("Please provide details regarding your current employment and family situation to help us assess your eligibility for economic support.")
        
        if st.button("🔄 Switch to Enablement Form", key="switch_to_enablement_from_support", help="Click here if you intended to apply for career enablement instead."):
            st.session_state.choice = "enablement" # Ensure the choice is updated
            st.session_state.step = 6 # Go to Enablement Personal Info step
            # Optionally clear support-specific form data if any was stored
            if "applicant_data" in st.session_state and st.session_state.get("applicant_data_type") == "support":
                del st.session_state.applicant_data
                if "applicant_data_type" in st.session_state: del st.session_state.applicant_data_type
            st.experimental_rerun()
        st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

        # Initialize or retrieve form data specific to this path
        form_data_support = st.session_state.get("applicant_data", {} if st.session_state.get("applicant_data_type") != "support" else st.session_state.get("applicant_data", {}))


        emirates_id_val = st.session_state.get("emirates_id", "N/A")
        st.text_input("Emirates ID (from scan)", value=emirates_id_val, disabled=True, key="support_form_eid")
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

        # Employment Status
        employed_options = ["Yes", "No"]
        default_employed_index_support = employed_options.index(form_data_support.get("CurrentlyEmployed", "No"))
        employed_status_support = st.radio(
            "Are you currently employed?", 
            options=employed_options, 
            key="support_employed_status", 
            horizontal=True,
            index=default_employed_index_support
        )
        form_data_support["CurrentlyEmployed"] = employed_status_support
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
        
        is_form_valid_support = True

        if employed_status_support == "No":
            form_data_support["employer_name"] = "N/A" # Clear or set to N/A if not employed
            last_salary_support = st.text_input(
                "What was your last drawn monthly salary in AED? (Enter numbers only)", 
                value=form_data_support.get("last_drawn_salary_value", ""), # Store raw value
                key="support_last_salary"
            )
            if last_salary_support and not last_salary_support.isdigit():
                st.warning("Please enter only numbers for salary.")
                is_form_valid_support = False
            form_data_support["last_drawn_salary_value"] = last_salary_support # Store raw value
            
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
            last_employment_date_support = st.date_input(
                "When was your last employment date?", 
                value=pd.to_datetime(form_data_support.get("last_employment_date_value"), errors='coerce').date() if form_data_support.get("last_employment_date_value") else None,
                key="support_last_employment_date",
                max_value=datetime.date.today() # Cannot be a future date
            )
            form_data_support["last_employment_date_value"] = str(last_employment_date_support) if last_employment_date_support else ""


            if not last_salary_support:
                is_form_valid_support = False
                st.warning("Last drawn salary is required if unemployed.")
            if not last_employment_date_support:
                is_form_valid_support = False
                st.warning("Last employment date is required if unemployed.")
        else: # Currently Employed
            form_data_support["last_employment_date_value"] = "N/A" # Clear or set to N/A
            current_employer_support = st.text_input(
                "Enter your current Employer's Name:", 
                value=form_data_support.get("employer_name", ""),
                key="support_current_employer"
            )
            form_data_support["employer_name"] = current_employer_support
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
            
            current_income_support_str = st.text_input(
                "What's your current total monthly income in AED? (Enter numbers only)", 
                value=form_data_support.get("current_monthly_income_value", ""), # Store raw value
                key="support_current_income"
            )
            if current_income_support_str and not current_income_support_str.isdigit():
                st.warning("Please enter only numbers for income.")
                is_form_valid_support = False
            form_data_support["current_monthly_income_value"] = current_income_support_str # Store raw value
            
            if not current_employer_support:
                is_form_valid_support = False
                st.warning("Employer name is required if currently employed.")
            if not current_income_support_str:
                is_form_valid_support = False
                st.warning("Current monthly income is required if currently employed.")

        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
        # Marital Status
        marital_options_support = ["Yes", "No"]
        default_marital_index_support = marital_options_support.index(form_data_support.get("marital_status", "No"))
        marital_status_support = st.radio(
            "Are you married?", 
            options=marital_options_support, 
            key="support_marital_status", 
            horizontal=True,
            index=default_marital_index_support
        )
        form_data_support["marital_status"] = marital_status_support
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

        # Number of Children
        num_children_support = st.number_input(
            "How many children do you have (under 18 years)?", 
            min_value=0, 
            step=1, 
            key="support_num_children",
            value=form_data_support.get("num_children", 0)
        )
        form_data_support["num_children"] = num_children_support

        st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        
        if st.button("➡️ Proceed to Document Upload", key="submit_support_personal_info", use_container_width=True):
            if is_form_valid_support:
                # Finalize form_data structure before saving to session_state
                final_form_data_support = {
                    "CurrentlyEmployed": form_data_support.get("CurrentlyEmployed"),
                    "marital_status": form_data_support.get("marital_status"),
                    "num_children": form_data_support.get("num_children")
                }
                if form_data_support.get("CurrentlyEmployed") == "No":
                    final_form_data_support["last_drawn_salary"] = f"{form_data_support.get('last_drawn_salary_value','0')} AED"
                    final_form_data_support["last_employment_date"] = form_data_support.get("last_employment_date_value","")
                    final_form_data_support["employer_name"] = "N/A"
                    final_form_data_support["current_monthly_income"] = "N/A"
                else:
                    final_form_data_support["employer_name"] = form_data_support.get("employer_name","")
                    final_form_data_support["current_monthly_income"] = f"{form_data_support.get('current_monthly_income_value','0')} AED"
                    final_form_data_support["last_drawn_salary"] = "N/A" # Or can be same as current income
                    final_form_data_support["last_employment_date"] = "N/A"

                st.session_state.applicant_data = final_form_data_support
                st.session_state.applicant_data_type = "support" # Mark data type
                st.session_state.step = 5 # Proceed to Support Document Upload
                st.experimental_rerun()
            else:
                st.error("Please correct the errors in the form before proceeding.")
    
    # --- Step 6: Social Economic Enablement Form ---
    elif st.session_state.step == 6:
        st.header("Step 6: Applicant Information (Economic Enablement)")
        st.write("Please provide details about your employment status, work domain, and upload your resume to help us assess your eligibility for enablement programs.")
        
        if st.button("🔄 Switch to Support Form", key="switch_to_support_from_enablement", help="Click here if you intended to apply for financial support instead."):
            st.session_state.choice = "support" # Ensure the choice is updated
            st.session_state.step = 4 # Go to Support Personal Info step
            # Optionally clear enablement-specific form data
            if "applicant_data" in st.session_state and st.session_state.get("applicant_data_type") == "enablement":
                del st.session_state.applicant_data
                if "applicant_data_type" in st.session_state: del st.session_state.applicant_data_type
                if "resume_filename" in st.session_state: del st.session_state.resume_filename # also clear resume flag
                if "resume_path" in st.session_state: del st.session_state.resume_path
            st.experimental_rerun()
        st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

        # Initialize or retrieve form data specific to this path
        form_data_enablement = st.session_state.get("applicant_data", {} if st.session_state.get("applicant_data_type") != "enablement" else st.session_state.get("applicant_data", {}))

        emirates_id_val_en = st.session_state.get("emirates_id", "N/A")
        st.text_input("Emirates ID (from scan)", value=emirates_id_val_en, disabled=True, key="enablement_form_eid")
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

        # Employment Status
        employed_options_en = ["Yes", "No"]
        default_employed_index_en = employed_options_en.index(form_data_enablement.get("CurrentlyEmployed", "No"))
        employed_status_en = st.radio(
            "Are you currently employed?", 
            options=employed_options_en, 
            key="enablement_employed_status", 
            horizontal=True,
            index=default_employed_index_en
        )
        form_data_enablement["CurrentlyEmployed"] = employed_status_en
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
        
        is_form_valid_enablement = True

        if employed_status_en == "No":
            form_data_enablement["employer_name"] = "N/A"
            last_salary_en = st.text_input(
                "What was your last drawn monthly salary in AED? (Enter numbers only)", 
                value=form_data_enablement.get("last_drawn_salary_value", ""),
                key="enablement_last_salary"
            )
            if last_salary_en and not last_salary_en.isdigit():
                st.warning("Please enter only numbers for salary.")
                is_form_valid_enablement = False
            form_data_enablement["last_drawn_salary_value"] = last_salary_en

            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
            last_employment_date_en = st.date_input(
                "When was your last employment date?", 
                value=pd.to_datetime(form_data_enablement.get("last_employment_date_value"), errors='coerce').date() if form_data_enablement.get("last_employment_date_value") else None,
                key="enablement_last_employment_date",
                max_value=datetime.date.today()
            )
            form_data_enablement["last_employment_date_value"] = str(last_employment_date_en) if last_employment_date_en else ""

            if not last_salary_en:
                is_form_valid_enablement = False
                st.warning("Last drawn salary is required if unemployed.")
            if not last_employment_date_en:
                is_form_valid_enablement = False
                st.warning("Last employment date is required if unemployed.")

        else: # Currently Employed
            form_data_enablement["last_employment_date_value"] = "N/A"
            current_employer_en = st.text_input(
                "Enter your current Employer's Name:", 
                value=form_data_enablement.get("employer_name", ""),
                key="enablement_current_employer"
            )
            form_data_enablement["employer_name"] = current_employer_en
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

            current_income_en_str = st.text_input(
                "What's your current total monthly income in AED? (Enter numbers only)", 
                value=form_data_enablement.get("current_monthly_income_value", ""),
                key="enablement_current_income"
            )
            if current_income_en_str and not current_income_en_str.isdigit():
                st.warning("Please enter only numbers for income.")
                is_form_valid_enablement = False
            form_data_enablement["current_monthly_income_value"] = current_income_en_str
            
            if not current_employer_en:
                is_form_valid_enablement = False
                st.warning("Employer name is required if currently employed.")
            if not current_income_en_str:
                is_form_valid_enablement = False
                st.warning("Current monthly income is required if currently employed.")


        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing
        # Work Domain
        work_domain_options = [
            "IT/Data Analyst", "Healthcare", "Education", "Construction", "Finance",
            "Retail", "Transportation", "Hospitality", "Marketing", "Manufacturing",
            "Arts/Entertainment", "Engineering", "Legal", "Human Resources", "Other"
        ]
        default_domain_index = work_domain_options.index(form_data_enablement.get("current_work_domain", "IT/Data Analyst")) if form_data_enablement.get("current_work_domain") in work_domain_options else 0
        current_work_domain_en = st.selectbox(
            "What is your current or most recent primary work domain/industry?", 
            options=work_domain_options, 
            key="enablement_work_domain",
            index=default_domain_index
        )
        form_data_enablement["current_work_domain"] = current_work_domain_en
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

        # Resume Upload
        uploaded_resume_file = st.file_uploader("Upload your Resume (PDF only, max 5MB)", type=["pdf"], key="enablement_resume_upload")
        
        # Display name of already uploaded resume if it exists in session and no new file is chosen
        if "resume_filename" in st.session_state and not uploaded_resume_file:
            st.info(f"Previously uploaded resume: `{st.session_state.resume_filename}`. You can upload a new one to replace it.")
        
        if uploaded_resume_file and not st.session_state.get("resume_filename"): # if new file uploaded and no prior one, or to replace
            if uploaded_resume_file.size > 5 * 1024 * 1024: # 5MB size limit
                st.error("Resume file size exceeds 5MB. Please upload a smaller file.")
                is_form_valid_enablement = False
            else:
                # Temporarily store the new file object if valid, process on submit
                st.session_state.new_resume_file_buffer = uploaded_resume_file 
        
        if not uploaded_resume_file and "new_resume_file_buffer" in st.session_state: # if user unselected after selecting
            del st.session_state.new_resume_file_buffer


        st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        if st.button("➡️ Proceed to Enablement Evaluation", key="submit_enablement_personal_info", use_container_width=True):
            # Resume validation: required if not already uploaded and stored in session_state
            if not st.session_state.get("resume_filename") and "new_resume_file_buffer" not in st.session_state:
                st.error("Resume upload is mandatory for the enablement path.")
                is_form_valid_enablement = False
            
            if is_form_valid_enablement:
                # Process and save new resume if uploaded
                if "new_resume_file_buffer" in st.session_state and st.session_state.new_resume_file_buffer:
                    resume_file_to_save = st.session_state.new_resume_file_buffer
                    sanitized_eid_for_resume = st.session_state.get("emirates_id", "default_resume_id").replace('-', '_').replace('/', '_').replace('\\', '_')
                    resume_filename_final = f"resume_{sanitized_eid_for_resume}_{time.time_ns()}.pdf" # Ensure unique name
                    resume_path_final = os.path.join(RESUME_DIR, resume_filename_final)
                    with open(resume_path_final, "wb") as f:
                        f.write(resume_file_to_save.getbuffer())
                    st.session_state.resume_filename = resume_filename_final # Store final filename
                    st.session_state.resume_path = resume_path_final         # Store final path
                    del st.session_state.new_resume_file_buffer # Clean up buffer
                
                # Finalize form_data structure
                final_form_data_enablement = {
                    "CurrentlyEmployed": form_data_enablement.get("CurrentlyEmployed"),
                    "current_work_domain": form_data_enablement.get("current_work_domain"),
                    "resume_filename": st.session_state.get("resume_filename"), # Get from session
                    "resume_path": st.session_state.get("resume_path")          # Get from session
                }
                if form_data_enablement.get("CurrentlyEmployed") == "No":
                    final_form_data_enablement["last_drawn_salary"] = f"{form_data_enablement.get('last_drawn_salary_value','0')} AED"
                    final_form_data_enablement["last_employment_date"] = form_data_enablement.get("last_employment_date_value","")
                    final_form_data_enablement["employer_name"] = "N/A"
                    final_form_data_enablement["current_monthly_income"] = "N/A"
                else:
                    final_form_data_enablement["employer_name"] = form_data_enablement.get("employer_name","")
                    final_form_data_enablement["current_monthly_income"] = f"{form_data_enablement.get('current_monthly_income_value','0')} AED"
                    final_form_data_enablement["last_drawn_salary"] = "N/A" 
                    final_form_data_enablement["last_employment_date"] = "N/A"

                st.session_state.applicant_data = final_form_data_enablement
                st.session_state.applicant_data_type = "enablement" # Mark data type
                st.session_state.step = 7 # Proceed to Enablement Evaluation
                st.experimental_rerun()
            else:
                st.error("Please correct the errors in the form and ensure resume is uploaded before proceeding.")


    # --- Step 5: Upload Financial Documents (Support Path) OR Evaluation Display ---
    elif st.session_state.step == 5:
        # Sub-state: Uploading documents
        if not st.session_state.get("evaluation_in_progress") and not st.session_state.get("evaluation_done"):
            st.header("Step 5: Upload Financial Documents (Economic Support)")
            st.write("For the Economic Support path, please upload your latest bank statement and credit report. This information is crucial for our financial assessment.")
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

            eid_val_docs = st.session_state.get("emirates_id", "N/A")
            st.text_input("Emirates ID (from scan)", value=eid_val_docs, disabled=True, key="financial_docs_eid")
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

            # Bank Statement Upload
            bank_statement_file = st.file_uploader(
                "Upload your latest 3-month bank statement (PDF, XLS, or XLSX, max 10MB)", 
                type=["pdf", "xls", "xlsx"], 
                key="upload_bank_statement",
                help="Ensure the statement clearly shows account activity for the last 3 months."
            )
            if bank_statement_file and bank_statement_file.size > 10 * 1024 * 1024: # 10MB limit
                st.error("Bank statement file size exceeds 10MB. Please upload a smaller file or split it.")
                bank_statement_file = None # Invalidate file
            
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # Spacing

            # Credit Report Upload
            credit_report_file = st.file_uploader(
                "Upload your latest Credit Report (PDF only, max 5MB)", 
                type=["pdf"], 
                key="upload_credit_report",
                help="A recent credit report from a recognized bureau (e.g., AECB)."
            )
            if credit_report_file and credit_report_file.size > 5 * 1024 * 1024: # 5MB limit
                st.error("Credit report file size exceeds 5MB. Please upload a smaller file.")
                credit_report_file = None # Invalidate file
            
            st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
            if st.button("🔒 Submit Documents & Start Evaluation", key="submit_financial_documents", use_container_width=True):
                if not bank_statement_file or not credit_report_file:
                    st.error("Both bank statement and credit report are required. Please upload them to proceed.")
                else:
                    # Process and save files
                    sanitized_eid_for_files = eid_val_docs.replace('-', '_').replace('/', '_').replace('\\', '_')
                    
                    bank_ext = bank_statement_file.name.split('.')[-1].lower()
                    bank_filename = f"bank_statement_{sanitized_eid_for_files}_{time.time_ns()}.{bank_ext}"
                    bank_file_path = os.path.join(BANK_DIR, bank_filename)
                    with open(bank_file_path, "wb") as f:
                        f.write(bank_statement_file.getbuffer())
                    st.session_state.bank_statement_path = bank_file_path
                    st.session_state.bank_statement_filename = bank_filename


                    credit_ext = credit_report_file.name.split('.')[-1].lower()
                    credit_filename = f"credit_report_{sanitized_eid_for_files}_{time.time_ns()}.{credit_ext}"
                    credit_file_path = os.path.join(CREDIT_DIR, credit_filename)
                    with open(credit_file_path, "wb") as f:
                        f.write(credit_report_file.getbuffer())
                    st.session_state.credit_report_path = credit_file_path
                    st.session_state.credit_report_filename = credit_filename
                    
                    st.session_state.evaluation_in_progress = True
                    st.session_state.evaluation_done = False # Reset flag for new evaluation
                    st.experimental_rerun()
        
        # Sub-state: Evaluation in progress
        elif st.session_state.get("evaluation_in_progress"):
            st.header("🔍 Running Background Checks (Economic Support)")
            st.markdown("We're currently evaluating your financial eligibility and reviewing your credit risk profile based on the documents provided. This process may take up to a minute. Please wait.")
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

            with st.spinner("Performing eligibility checks... Your patience is appreciated."):
                if not st.session_state.get("evaluation_done"): # Ensure this runs only once
                    time.sleep(5) # Simulate backend processing time
                    try:
                        payload_support_eval = {
                            "emirates_id": st.session_state.get("emirates_id"),
                            "applicant_data": st.session_state.get("applicant_data", {}),
                            "bank_statement_filename": st.session_state.get("bank_statement_filename"), # Send filename
                            "credit_report_filename": st.session_state.get("credit_report_filename")    # Send filename
                        }
                        
                        # --- Actual API Call to Social Economic Support Backend ---
                        support_eval_res = requests.post("http://localhost:5001/evaluate", json=payload_support_eval) 
                        
                        if support_eval_res.status_code == 200:
                            st.session_state.evaluation_result = support_eval_res.json()
                            # --- <<<< ASYNCHRONOUS API CALL ADDED HERE FOR SUPPORT PATH >>>> ---
                            # Call the submit API with the *evaluation result*
                            if st.session_state.get("emirates_id") and st.session_state.evaluation_result:
                                asyncio.run(call_submit_api_async(st.session_state.emirates_id, st.session_state.evaluation_result))
                                st.toast("Evaluation result sent for background processing.", icon="📤")
                            # --- <<<< END OF ASYNCHRONOUS API CALL >>>> ---
                        else:
                            st.session_state.evaluation_result = {"error": f"Support backend error: {support_eval_res.status_code} - {support_eval_res.text}"}
                    
                    except requests.exceptions.ConnectionError:
                        st.session_state.evaluation_result = {"error": "Could not connect to the Social Economic Support backend server. Please ensure it's running and accessible."}
                    except Exception as e:
                        st.session_state.evaluation_result = {"error": f"An unexpected error occurred during support evaluation: {str(e)}"}
                    
                    st.session_state.evaluation_done = True # Mark evaluation as complete
                    st.session_state.evaluation_in_progress = False # End "in_progress" state
                    st.experimental_rerun() # Rerun to display results
            
        # Sub-state: Evaluation done, display results
        elif st.session_state.get("evaluation_done"):
            st.header("✅ Evaluation Complete (Economic Support)")
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
            
            display_evaluation_result(st.session_state.get("evaluation_result", {}), "Social Economic Support")
            
            st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
            if st.button("🏁 Return to Home Page", key="support_eval_return_home", use_container_width=True):
                # Clear all session state for a fresh start
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.step = 0 # Go to home
                st.experimental_rerun()

    # --- Step 7: Enablement Path - Evaluation Display ---
    elif st.session_state.step == 7:
        # This step assumes evaluation is triggered and results are displayed.
        # The "evaluation_in_progress" state is managed by "enablement_evaluation_done".
        
        if not st.session_state.get("enablement_evaluation_done"): # If not yet evaluated
            st.header("🔍 Evaluating Career Enablement Eligibility")
            st.markdown("We're analyzing your resume and application details to assess your eligibility for enablement programs. This may take a moment. Please wait.")
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)

            with st.spinner("Processing enablement evaluation... Your patience is appreciated."):
                time.sleep(5) # Simulate backend processing time
                try:
                    payload_enablement_eval = {
                        "emirates_id": st.session_state.get("emirates_id"),
                        "applicant_data": st.session_state.get("applicant_data", {}),
                        "resume_filename": st.session_state.get("applicant_data",{}).get("resume_filename") # From applicant_data
                    }
                    
                    # --- Actual API Call to Social Economic Enablement Backend ---
                    enablement_eval_res = requests.post("http://localhost:8001/evaluate", json=payload_enablement_eval)
                    
                    if enablement_eval_res.status_code == 200:
                        st.session_state.evaluation_result = enablement_eval_res.json() # Store result
                        # --- <<<< ASYNCHRONOUS API CALL ADDED HERE FOR ENABLEMENT PATH >>>> ---
                        # Call the submit API with the *evaluation result*
                        if st.session_state.get("emirates_id") and st.session_state.evaluation_result:
                            asyncio.run(call_submit_api_async(st.session_state.emirates_id, st.session_state.evaluation_result))
                            st.toast("Evaluation result sent for background processing.", icon="📤")
                        # --- <<<< END OF ASYNCHRONOUS API CALL >>>> ---
                    else:
                        st.session_state.evaluation_result = {"error": f"Enablement backend error: {enablement_eval_res.status_code} - {enablement_eval_res.text}"}
                
                except requests.exceptions.ConnectionError:
                    st.session_state.evaluation_result = {"error": "Could not connect to the Social Economic Enablement backend server. Please ensure it's running and accessible."}
                except Exception as e:
                    st.session_state.evaluation_result = {"error": f"An unexpected error occurred during enablement evaluation: {str(e)}"}
                
                st.session_state.enablement_evaluation_done = True # Mark as done for this path
                # Note: We use 'evaluation_result' as a common key for storing results from either path
                st.experimental_rerun() # Rerun to display results

        else: # Enablement evaluation is done, display results
            st.header("✅ Evaluation Complete (Economic Enablement)")
            st.markdown("<hr style='margin-top:10px; margin-bottom:20px;'>", unsafe_allow_html=True)
            
            display_evaluation_result(st.session_state.get("evaluation_result", {}), "Social Economic Enablement")
            
            st.markdown("<hr style='margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
            if st.button("🏁 Return to Home Page", key="enablement_eval_return_home", use_container_width=True):
                # Clear all session state for a fresh start
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.step = 0 # Go to home
                st.experimental_rerun()

if __name__ == "__main__":
    # Workaround for asyncio in Streamlit if needed for older versions or specific setups
    # For newer Streamlit, asyncio.run might work directly in callbacks for background tasks
    # that don't update UI immediately.
    # If issues, consider threading for the async call if it's truly fire-and-forget.
    main()