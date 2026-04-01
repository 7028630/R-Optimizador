import streamlit as st
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 

# Dictionary to map tabs. Format: "MONTH YEAR": "GID"
# You just add new lines here as you create new months in Google Sheets
MONTH_GIDS = {
    "ABRIL 2026": "767368955", 
    "MAYO 2026": "0", 
}

BASE_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid="

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; }
    header, [data-testid="stHeader"] { background-color: #17202A !important; }
    [data-testid="stSidebar"] { background-color: #111821 !important; }
    .abs-container { background-color: #212F3C; padding: 20px; border-radius: 10px; border-left: 5px solid #C0392B; color: white; }
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .custom-table th { background-color: #2C3E50; border-bottom: 2px solid #C0392B; padding: 12px; text-align: left; color: white; }
    .custom-table td { border-bottom: 1px solid #34495E; padding: 10px; color: white; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    .date-tooltip { cursor: help; border-bottom: 2px dotted #E74C3C; color: #E74C3C; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Initialize Session States
for key in ['final_ranking', 'abs_list', 'manual_mode', 'show_turns']:
    if key not in st.session_state: st.session_state[key] = [] if 'list' in key or 'ranking' in key else False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 📅 Periodo")
    sel_month = st.selectbox("Mes:", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=3)
    sel_year = st.selectbox("Año:", [2025, 2026, 2027], index=1)
    
    lookup_key = f"{sel_month} {sel_year}"
    CURRENT_GID = MONTH_GIDS.get(lookup_key, "0")
    SHEET_URL = f"{BASE_URL}{CURRENT_GID}"

    st.write("---")
    sidebar_limit = st.number_input("Mostrar hasta ID:", min_value=1, max_value=21, value=14)
    
    # ... (Keep your toggles and turns logic here) ...

# --- MAIN CONTENT ---
st.title(f"📦 Panel: {lookup_key}")

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i, abs_temp = {}, {}, {}

    def extract_id(link):
        match = re.search(r'id=(\d+)', str(link))
        return int(match.group(1)) if match else None

    try:
        df_raw = pd.read_csv(SHEET_URL)
        for _, row in df_raw.iterrows():
            sid = extract_id(row.iloc[1]) # Col B
            if sid and sid <= sidebar_limit:
                p_val = pd.to_numeric(str(row.iloc[6]).replace('.',''), errors='coerce') or 0 # Col G
                i_val = pd.to_numeric(str(row.iloc[7]).replace('.',''), errors='coerce') or 0 # Col H
                date_val = str(row.iloc[0]) # Col A
                
                data_p[sid] = data_p.get(sid, 0) + p_val
                data_i[sid] = data_i.get(sid, 0) + i_val
                
                if p_val == 0:
                    if sid not in abs_temp: abs_temp[sid] = []
                    abs_temp[sid].append(date_val)

        # Process Results
        abs_data = [{"Surtidor": f"Surtidor {s}", "ID": s, "Count": len(abs_temp.get(s, [])), "Dates": ", ".join(abs_temp.get(s, []))} for s in range(1, sidebar_limit + 1)]
        ranking_data = [{"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)} for s in range(1, sidebar_limit + 1)]
        
        st.session_state.abs_list = abs_data
        st.session_state.final_ranking = sorted(ranking_data, key=lambda x: x['Pedidos'], reverse=True)
        st.rerun()
    except Exception as e:
        st.error(f"Error: Asegúrate de que el GID para {lookup_key} sea correcto.")

# --- DISPLAY & EXPORT ---
if st.session_state.final_ranking:
    # --- Visualization Code (Pie Chart & Ranking Table) ---
    # ... (Keep your Plotly and Ranking Table code here) ...

    st.write("---")
    st.markdown("### ⚠️ AUSENCIAS")
    # ... (Keep your Absencias Table code here) ...

    # --- NEW: EXPORT SECTION ---
    st.write("---")
    st.markdown("### 📥 Exportar Datos")
    col_ex1, col_ex2 = st.columns(2)
    
    df_rank_export = pd.DataFrame(st.session_state.final_ranking)
    df_abs_export = pd.DataFrame(st.session_state.abs_list)

    with col_ex1:
        st.download_button(label="📊 Descargar Ranking (CSV)", data=df_rank_export.to_csv(index=False), file_name=f"Ranking_{lookup_key}.csv", mime="text/csv")
    
    with col_ex2:
        st.download_button(label="❌ Descargar Ausencias (CSV)", data=df_abs_export.to_csv(index=False), file_name=f"Ausencias_{lookup_key}.csv", mime="text/csv")
