import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt
import seaborn as sns
import re
import textwrap
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# =========================
# LLM (Ollama)
# =========================
def ask_llm(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


# =========================
# Load Default Data
# =========================
@st.cache_data
def load_default_data():
    return yf.download("^BSESN", period="1y")


# =========================
# Clean Code
# =========================
def clean_code(code):
    code = re.sub(r"```.*?\n", "", code)
    code = re.sub(r"```", "", code)
    return textwrap.dedent(code.strip())


# =========================
# Safe Code Filter
# =========================
def safe_clean_code(code):
    forbidden = ["read_csv", "to_csv", "open(", "path/to"]
    return "\n".join([line for line in code.split("\n") if not any(f in line for f in forbidden)])


# =========================
# Generate Code
# =========================
def generate_code(user_query, schema):
    prompt = f"""
You are a Python data analyst.

Dataset schema:
{schema}

RULES:
- Use existing dataframe df
- Do not load data
- Return only Python code

User query:
{user_query}
"""
    return ask_llm(prompt)


# =========================
# Generate Insights (for PDF)
# =========================
def generate_insights(schema):
    prompt = f"""
Analyze this dataset:
{schema}

Give key insights, trends, and risks.
"""
    return ask_llm(prompt)


# =========================
# PDF Generator
# =========================
def create_pdf(text):
    file_path = "report.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph(text, styles["Normal"]))

    doc.build(content)
    return file_path


# =========================
# UI START
# =========================
st.set_page_config(page_title="Agentic AI Analyst", layout="wide")

st.title("🤖 Agentic AI Data Analyst")

# =========================
# DATA SOURCE
# =========================
st.sidebar.header("📁 Data Source")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = load_default_data()

st.subheader("📊 Data Preview")
st.dataframe(df.head())

# Schema
schema = {
    "columns": df.columns.tolist(),
    "shape": df.shape
}

# =========================
# BUTTON UI
# =========================
st.markdown("## ⚡ Quick Insights")

col1, col2, col3 = st.columns(3)

if col1.button("📊 Summary"):
    st.write(df.describe())

if col2.button("🔥 Correlation"):
    plt.figure(figsize=(8,5))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm")
    st.pyplot(plt)

if col3.button("📈 Trend"):
    if 'Close' in df.columns:
        df['Close'].plot(figsize=(10,5))
        st.pyplot(plt)

# =========================
# CHAT MEMORY
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

st.markdown("## 💬 Chat with Data")

user_input = st.text_input("Ask your question")

if user_input:
    st.session_state.history.append(("User", user_input))

    code = generate_code(user_input, schema)
    code = safe_clean_code(clean_code(code))

    st.code(code, language="python")

    try:
        exec(code)
        st.pyplot(plt)
        st.success("✅ Done")
    except Exception as e:
        st.error(f"Error: {e}")

    st.session_state.history.append(("AI", "Analysis done"))

# Show chat history
for role, msg in st.session_state.history:
    st.write(f"**{role}:** {msg}")

# =========================
# PDF REPORT
# =========================
st.markdown("## 📄 Generate Report")

if st.button("Generate PDF Report"):
    insights = generate_insights(schema)
    pdf_path = create_pdf(insights)

    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download Report", f, file_name="EDA_Report.pdf")