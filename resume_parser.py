import streamlit as st
from pdfminer.high_level import extract_text
import docx2txt
import spacy
nlp=spacy.load('en_core_web_sm')
from spacy.matcher import Matcher
import phonenumbers
import re
import pandas as pd
import csv
import pdfplumber
import time
import os

st.set_page_config(
    page_title="Resume Parser",
    page_icon=":clipboard:",
    layout="wide",
    initial_sidebar_state="expanded",
)
def add_background_image(image_path):
    import os
    import base64

    # Validate image path
    if not os.path.exists(image_path):
        st.error(f"Image not found: {image_path}")
        return

    # Encode image to base64
    with open(image_path, "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()

    # Apply as background
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded_image}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Call the function with your image
add_background_image("background.jpg")
def extract_text_file(file_path):
    if file_path is not None:
        file_name = file_path.name  # Get the file name
        if file_name.lower().endswith(".pdf"):
            return extract_text(file_path)
        elif file_name.lower().endswith(".docx"):
            return docx2txt.process(file_path)
        elif file_name.lower().endswith(".txt"):
            # Read and return the content of the uploaded text file
            return (file_path.getvalue().decode('utf-8'))
        else:
            raise ValueError("Unsupported file format")
    else:
        return ""  # Return an empty string if no file is uploaded
    

def extract_name(resume_text):
    nlp = spacy.load('en_core_web_sm')
    matcher = Matcher(nlp.vocab)

    # Define name patterns
    patterns = [
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}],  # First name, Middle name, and Last name
        [{'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}, {'POS': 'PROPN'}]  # First name, Middle name, Middle name, and Last name
       
    ]

    for pattern in patterns:
        matcher.add('NAME', patterns=[pattern])

    doc = nlp(resume_text)
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        return span.text

    return "Not Found"


def extract_contact_num(text):
    try:
        # Try to find a phone number using phonenumbers library
        phone_matches = list(phonenumbers.PhoneNumberMatcher(text, None))
        if phone_matches:
            return phone_matches[0].raw_string
    except:
        pass

    # If the phonenumbers library approach fails or no phone number is found, use regex
    phone_regex = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})'
    match = re.search(phone_regex, text)
    if match:
        return match.group()

    return "Not Found"


def extract_email(text):
    # Use regex pattern to find a potential email address
    pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return "Not Found"


def extract_skills(resume_text):
    nlp = spacy.load("en_core_web_sm")
    nlp_text = nlp(resume_text)

    # Removing stop words and implementing word tokenization
    tokens = [token.text for token in nlp_text if not token.is_stop]

    # Reading the CSV file containing skills
    data = pd.read_csv("Skills.csv")

    # Extract skill names from CSV
    skills = set(data.columns.str.lower())

    skillset = []

    # Check for one-grams (e.g., "python")
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)

    # Check for bi-grams and tri-grams (e.g., "machine learning")
    noun_chunks = list(nlp_text.noun_chunks)
    for chunk in noun_chunks:
        token = chunk.text.lower().strip()
        if token in skills:
            skillset.append(token)

    skills_string = ', '.join(set([i.capitalize() for i in skillset]))

    return skills_string if skills_string else "Not Found"


import re

def extract_education(text):
    education = []

    # List of education keywords to match against
    education_keywords = [
        'BE', 'B.E.', 'B.E', 'BS', 'B.S', 'C.A.', 'c.a.', 'B.Com', 'B. Com', 'M. Com', 'M.Com', 'M. Com .',
        'ME', 'M.E', 'M.E.', 'MS', 'M.S', 'Bsc', 'Msc', 'B. Pharmacy', 'B Pharmacy', 'M. Pharmacy',
        'BTECH', 'B.TECH', 'M.TECH', 'MTECH',
        'PHD', 'phd', 'ph.d', 'Ph.D.', 'MBA', 'mba', 'graduate', 'post-graduate', '5 year integrated masters', 'masters',
        'Bachelor of Technology', 'Master of Technology', 'CSE', 'ECE', 'EEE', 'Information Technology',
        'Mechanical Engineering', 'Computer Science and Engineering',
        'Electronics and Communication Engineering', 'Electrical and Electronics Engineering'
    ]

    for keyword in education_keywords:
        pattern = r"(?i)\b{}\b".format(re.escape(keyword))
        match = re.search(pattern, text)
        if match:
            education.append(match.group())

    education = [edu for edu in education if edu.upper() != 'BE' and edu.upper() != 'ME']
    education_string = ', '.join(education)

    return education_string if education_string else "Not Found"

import csv

languages_list = []

# Specify the path to your CSV file
csv_file_path = "language-codes_csv.csv"

# Read the languages from the CSV file
with open(csv_file_path, "r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        language = row[1].strip()
        if language:
            languages_list.append(language.lower())  

def extract_language(text):
    text = text.lower()  
    languages = set()  
    for language in languages_list:
        pattern = r"\b{}\b".format(re.escape(language))
        match = re.search(pattern, text)
        if match:
            languages.add(language)

    if languages:
        capitalized_languages = [lang.title() for lang in languages]
        languages_string = ', '.join(capitalized_languages)
        return languages_string
    else:
        return "Not Found"  


keywords_to_search=['institute of','college of','university',
                    'engineering college','polytechnic college','polytechnic',
                    'vishwavidyalaya','academy of','academy']


def extract_university(text, keywords):
    lines = text.split('\n')
    keyword_pattern = r"(?i)\b(" + "|".join(map(re.escape, keywords)) + r")\b"
    
    for line in lines:
        if re.search(keyword_pattern, line):
            return line.strip()
    
    return "Not Found"  


def extract_links(text):
    # Regular expression patterns for LinkedIn and GitHub URLs
    linkedin_pattern = r"(https?://)?(www\.)?linkedin\.com/in/([a-zA-Z0-9.-]+)"
    github_pattern = r"(?:https:\/\/)?(?:www\.)?github\.com\/[^/]+$"

    # Search for LinkedIn and GitHub links in the text
    linkedin_links = re.findall(linkedin_pattern, text)
    github_links = re.findall(github_pattern, text)

    # Filter out empty matches and construct valid URLs
    linkedin_links = [f"https://www.linkedin.com/in/{link[2]}" for link in linkedin_links if link[2]]
    github_links = [f"https://github.com/{link[2]}" for link in github_links if link[2]]

    return linkedin_links, github_links


def extract_hyperlinks(uploaded_file):
    linkedin_links = []
    github_links = []

    # Check the file extension to determine the type
    file_extension = uploaded_file.name.split('.')[-1].lower()

    if file_extension == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page_no in range(len(pdf.pages)):
                page = pdf.pages[page_no]
                hyperlinks = page.hyperlinks

                if hyperlinks:
                    for hyperlink in hyperlinks:
                        url = hyperlink.get('uri', 'N/A')

                        if not url.lower().startswith("mailto:") and "gmail.com" not in url.lower():
                            if "linkedin.com/in/" in url:
                                linkedin_links.append(url)
                            elif "github.com/" in url and not url.lower().count("/") >= 4:
                                github_links.append(url)
                else:
                    text = page.extract_text()
                    page_linkedin_links, page_github_links = extract_links(text)
                    linkedin_links.extend(page_linkedin_links)
                    github_links.extend(page_github_links)
    elif file_extension == "docx":
        text = docx2txt.process(uploaded_file)
        page_linkedin_links, page_github_links = extract_links(text)
        linkedin_links.extend(page_linkedin_links)
        github_links.extend(page_github_links)
    elif file_extension == "txt":
        text = uploaded_file.read().decode("utf-8")
        page_linkedin_links, page_github_links = extract_links(text)
        linkedin_links.extend(page_linkedin_links)
        github_links.extend(page_github_links)
    else:
        st.error("Unsupported file format. Please provide a PDF, DOCX, or TXT file.")

    return linkedin_links, github_links



def extract_information():
    name = extract_name(text)
    contact_number = extract_contact_num(text)
    email = extract_email(text)
    education_details = extract_education(text)
    education_institute = extract_university(text, keywords_to_search)
    skills = extract_skills(text)
    languages_spoken = extract_language(text)
    linkedin_links, github_links = extract_hyperlinks(uploaded_file)
    linkedin_found = False
    github_found = False
    if linkedin_links:
        li_link=linkedin_links[0]
        lin_link = '<a href="{}" target="_blank">{}</a>'.format(li_link, li_link)
        linkedin_found = True

    if not linkedin_found:
        lin_link='Not Found'

    if github_links:
        gh_link=github_links[0]
        git_link = '<a href="{}" target="_blank">{}</a>'.format(gh_link, gh_link)
        github_found = True

    if not github_found:
        git_link='Not Found'
        

    if email!='Not Found':
        email = '<a href="mailto:{}">{}</a>'.format(email, email)

    return {'Name':name,
            'Contact Number':contact_number,
            'Mail ID':email,
            'Education Details':education_details,
            'Education Institute':education_institute,
            'Technical Skills':skills,
            'Languages Known':languages_spoken,
            'LinkedIn Profile':lin_link,
            'GitHub Profile':git_link
            }


#Function for styling Streamlit elements
def apply_custom_styles():
    st.markdown("""
    <style>
    .css-1b3k30v {
        background-color: #f44336 !important; /* Red color */
        border-radius: 10px;
        padding: 20px;
    }
    .css-1kj8j5t {
        background-color: #f44336 !important; /* Red color */
        color: white !important; /* Text color */
    }
    .css-1m6v8dt {
        background-color: #f44336 !important; /* Red color */
        color: white !important; /* Text color */
    }
    .css-1m6v8dt:hover {
        background-color: #d32f2f !important; /* Darker red on hover */
    }
    </style>
    """,
    unsafe_allow_html=True
)

apply_custom_styles()

progress_bar = st.progress(0)
for percent_complete in range(100):
    time.sleep(0.01)  # Simulating processing time
    progress_bar.progress(percent_complete + 1)
st.title("Resume Parser")
st.header("Extract Valuable Information from Resumes")
uploaded_files = st.file_uploader("Upload Single/Multiple file(s) (PDF/WORD/TEXT)", type=['pdf', 'docx', 'txt'], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        text = extract_text_file(uploaded_file)

        if text:
            st.subheader(f"Processing Resume: {uploaded_file.name}")
            parsed_info = extract_information()

            st.markdown('**Scroll down**:arrow_down: to see the full details')
            st.subheader("Parsed Content")

            # Create a DataFrame for parsed information and remove headers, indexes
            df = pd.DataFrame(parsed_info.items(), columns=["Keys", "Values"])

            # Custom table styling with colors and hover effect
            table_style = """
            <style>
            .table-container {
                max-height: 500px;
                overflow-y: scroll;
                margin-top: 20px;
            }

            table {
                border-collapse: collapse;
                width: 100%;
                background-color: #f9f9f9;
            }

            th, td {
                padding: 12px;
                text-align: left;
                font-family: Arial, sans-serif;
            }

            th {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }

            td {
                background-color: #f1f1f1;
                border-bottom: 1px solid #ddd;
            }

            td:first-child {
                font-weight: bold;
                color: #2C3E50;
            }

            td:nth-child(2) {
                color: #34495E;
            }

            tr:hover td {
                background-color: #E8F4E8; /* Light green on hover */
                cursor: pointer;
            }

            .resume-details {
                margin-bottom: 20px;
            }

            .footer {
                font-size: 12px;
                color: #888;
                text-align: center;
                margin-top: 20px;
            }

            </style>
            """
            st.markdown(table_style, unsafe_allow_html=True)  # Apply the table style

            # Display the table with custom styling
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.write(df.to_html(index=False, header=True, escape=False), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)



# Add footer for 'Created by Srujay' on the right side
st.markdown("""
    <style>
        /* Footer styles for 'Created by Srujay' */
        .footer-right {
            position: fixed;
            bottom: 10px;   /* Slight distance from the bottom */
            right: 10px;    /* Align to the right edge */
            font-size: 14px;
            color: #333;    /* Dark color for text */
            background-color: transparent;
            z-index: 1000;
            text-align: right;  /* Align text to the right */
        }
    </style>
    <div class="footer-right">
        Created by Srujay
    </div>
""", unsafe_allow_html=True)
