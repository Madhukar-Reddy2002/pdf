import streamlit as st
import PyPDF2
import re
import pandas as pd
import os
import tempfile
from datetime import datetime
import base64

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        num_pages = len(pdf_reader.pages)
        all_page_text = []
        for page_num in range(num_pages):
            # Get the page
            page = pdf_reader.pages[page_num]
            
            # Extract text from the page
            page_text = page.extract_text()
            clean_text = re.sub(r'[^\x00-\x7F]+', '', page_text)
            
            # Append the text to the list
            all_page_text.append(clean_text)
            
        return all_page_text

def process_transactions_text(all_text):
    pages = []
    for i in all_text:
        li = i.split('\n')
        li2 = li[1::2]
        pages.append(li2)

    transactions_text = []
    pattern = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b.*?)(?=Transaction\sID)"
    for page in pages:
        page_text = " ".join(page)
        matches = re.findall(pattern, page_text)
        transactions_text.append(matches)

    text = transactions_text[0][0]
    text = text.split(" ")
    start = text.index("Amount")
    text = " ".join(text[start+1:])
    transactions_text[0][0] = text

    transactions_nice = []
    for transaction_page in transactions_text:
        for transaction in transaction_page:
            # Split the transaction string by spaces and strip each substring
            stripped_transaction = transaction.split(" ")
            cleared_transaction = [substr.strip() for substr in stripped_transaction if substr.strip()]
            
            # Process each cleared transaction
            month = cleared_transaction[0]
            date = cleared_transaction[1].rstrip(',')
            year = cleared_transaction[2]
            time = cleared_transaction[3] + " " + cleared_transaction[4]
            transaction_date = datetime.strptime(f"{month} {date} {year} {time}", "%b %d %Y %I:%M %p")

            data = {
                "date": transaction_date,
                "type": cleared_transaction[5],
                "amount": cleared_transaction[6],
                "payee": " ".join(cleared_transaction[9:])
            }
            transactions_nice.append(data)

    return transactions_nice

def main():
    st.title("PDF Transaction Extractor")
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            all_text = extract_text_from_pdf(temp_file.name)

        transactions_nice = process_transactions_text(all_text)
        df = pd.DataFrame(transactions_nice)
        st.write("Extracted DataFrame:")
        st.write(df)

        # Add a download button for the CSV file
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="transactions.csv">Download CSV File</a>'
        st.markdown(href, unsafe_allow_html=True)

        # Clean up the temporary file
        os.unlink(temp_file.name)

if __name__ == "__main__":
    main()