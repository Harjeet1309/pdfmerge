import streamlit as st
import pandas as pd
import tabula

st.set_page_config(page_title="PDF Data Joiner", layout="wide")

st.title("📄 PDF Data Joiner")
st.write("Upload two PDFs — I’ll find the common table data automatically!")

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

def auto_common_rows(df1, df2):
    # Convert all data to string for comparison
    df1_str = df1.astype(str)
    df2_str = df2.astype(str)
    
    # Find columns with similar names (fuzzy matching)
    from fuzzywuzzy import fuzz
    col_matches = []
    for c1 in df1_str.columns:
        for c2 in df2_str.columns:
            if fuzz.ratio(c1.lower(), c2.lower()) > 80:
                col_matches.append((c1, c2))
    
    if not col_matches:
        return None  # fallback if no similar columns
    
    # Merge on all matched columns
    left_cols, right_cols = zip(*col_matches)
    common_df = pd.merge(df1_str, df2_str, left_on=left_cols, right_on=right_cols, how="inner")
    return common_df

if uploaded_file1 and uploaded_file2:
    with st.spinner("🔍 Extracting and comparing PDFs..."):
        df1 = extract_tables(uploaded_file1)
        df2 = extract_tables(uploaded_file2)

        if df1 is not None and df2 is not None:
            st.success("✅ Tables detected in both PDFs.")

            common_df = auto_common_rows(df1, df2)
            if common_df is not None and not common_df.empty:
                st.dataframe(common_df)
                csv = common_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download Common Data as CSV", csv, "common_data.csv", "text/csv")
            else:
                st.warning("No common rows found automatically.")
        else:
            st.error("❌ No tables detected in one or both PDFs.")
