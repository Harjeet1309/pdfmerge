import streamlit as st
import pandas as pd
import pdfplumber
import tabula
from fuzzywuzzy import fuzz
from io import BytesIO
import re

st.set_page_config(page_title="PDF Data Joiner", layout="wide")
st.title("📄 PDF Data Joiner")
st.write("Upload two PDFs — I’ll find common tables or text and generate proper CSV!")

uploaded_file1 = st.file_uploader("Upload First PDF", type=["pdf"])
uploaded_file2 = st.file_uploader("Upload Second PDF", type=["pdf"])

def extract_tables(file):
    try:
        tables = tabula.read_pdf(file, pages="all", multiple_tables=True)
        if tables and len(tables) > 0:
            df = pd.concat(tables, ignore_index=True)
            return df
    except:
        return None
    return None

def extract_text(file):
    text_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_data.extend(page_text.split("\n"))
    return list(set(text_data))

def parse_text_table(lines):
    # Try to detect header
    header = None
    for line in lines:
        if re.search(r"RollNo|Name|Department|Grade", line, re.IGNORECASE):
            header = line.split()
            break

    # Parse remaining rows
    rows = []
    for line in lines:
        if header and line != " ".join(header):
            rows.append(line.split())
    if header and len(rows[0]) == len(header):
        df = pd.DataFrame(rows, columns=header)
    else:
        df = pd.DataFrame(rows)
    return df

def find_common_text(text1, text2):
    common = []
    for t1 in text1:
        for t2 in text2:
            if fuzz.token_set_ratio(t1, t2) > 85:
                common.append(t1)
                break
    return list(set(common))

if uploaded_file1 and uploaded_file2:
    with st.spinner("🔍 Extracting and comparing PDFs..."):
        df1 = extract_tables(uploaded_file1)
        uploaded_file1.seek(0)
        df2 = extract_tables(uploaded_file2)

        if df1 is not None and df2 is not None:
            st.success("✅ Found tables in both PDFs. Performing automatic join...")
            # Auto column matching
            join_cols = []
            for col1 in df1.columns:
                for col2 in df2.columns:
                    if fuzz.ratio(str(col1).lower(), str(col2).lower()) > 80:
                        join_cols.append((col1, col2))
            if join_cols:
                col1, col2 = join_cols[0]
                common_df = pd.merge(df1, df2, left_on=col1, right_on=col2, how="inner")
                st.dataframe(common_df)
                csv = common_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, "common_data.csv", "text/csv")
            else:
                st.warning("⚠️ No matching columns found to join automatically.")
        else:
            st.info("🧾 No tables found. Parsing text into proper table...")
            text1 = extract_text(uploaded_file1)
            text2 = extract_text(uploaded_file2)
            common_text = find_common_text(text1, text2)

            if common_text:
                df_text = parse_text_table(common_text)
                st.dataframe(df_text)
                csv = df_text.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, "common_text_data.csv", "text/csv")
            else:
                st.error("❌ No common text found.")
