import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

st.title("PDF Reader")

# Local file
pdf_viewer("/Users/r/Desktop/Wohnraummietvertrag-Entwurf 20260721.pdf")

# File upload
uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
if uploaded_file:
    pdf_viewer(uploaded_file.getvalue())