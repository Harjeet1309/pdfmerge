from flask import Flask, request, jsonify, send_file
import pandas as pd
import pdfplumber
import tabula
from fuzzywuzzy import fuzz
from io import BytesIO

app = Flask(__name__)

# Extract tables from PDF
def extract_tables(file):
    try:
        tables = tabula.read_pdf(file, pages="all", multiple_tables=True)
        if tables and len(tables) > 0:
            df = pd.concat(tables, ignore_index=True)
            return df
    except:
        return None
    return None

# Extract text from PDF
def extract_text(file):
    text_data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_data.extend(page_text.split("\n"))
    return list(set(text_data))

# Find common text
def find_common_text(text1, text2):
    common = []
    for t1 in text1:
        for t2 in text2:
            if fuzz.token_set_ratio(t1, t2) > 85:
                common.append(t1)
                break
    return list(set(common))

@app.route("/compare", methods=["POST"])
def compare_pdfs():
    if 'pdf1' not in request.files or 'pdf2' not in request.files:
        return jsonify({"error": "Please upload both PDFs"}), 400
    
    file1 = request.files['pdf1']
    file2 = request.files['pdf2']

    # Try table extraction
    df1 = extract_tables(file1)
    file1.seek(0)  # reset file pointer
    df2 = extract_tables(file2)
    
    if df1 is not None and df2 is not None:
        # Attempt auto column matching
        join_cols = []
        for col1 in df1.columns:
            for col2 in df2.columns:
                if fuzz.ratio(str(col1).lower(), str(col2).lower()) > 80:
                    join_cols.append((col1, col2))
        if join_cols:
            col1, col2 = join_cols[0]
            common_df = pd.merge(df1, df2, left_on=col1, right_on=col2, how="inner")
            # Convert to CSV in-memory
            buffer = BytesIO()
            common_df.to_csv(buffer, index=False)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name="common_data.csv", mimetype="text/csv")
        else:
            return jsonify({"error": "No matching columns found in tables"}), 200
    else:
        # Fallback: text comparison
        file1.seek(0)
        file2.seek(0)
        text1 = extract_text(file1)
        text2 = extract_text(file2)
        common_text = find_common_text(text1, text2)
        if common_text:
            return jsonify({"common_text": common_text})
        else:
            return jsonify({"error": "No common text found"}), 200

if __name__ == "__main__":
    app.run(debug=True)
