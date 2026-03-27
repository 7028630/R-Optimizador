import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

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
    
    /* Table Styling */
    .abs-container { background-color: #212F3C; padding: 20px; border-radius: 10px; border-left: 5px solid #C0392B; color: white; }
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .custom-table th { background-color: #2C3E50; border-bottom: 2px solid #C0392B; padding: 12px; text-align: left; color: white; }
    .custom-table td { border-bottom: 1px solid #34495E; padding: 10px; color: white; }
    
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    
    .date-tooltip { cursor: help; border-bottom: 2px dotted #E74C3C; color: #E74C3C; font-weight: bold; }
    
    div[data-testid="stNumberInput"] { width: 100px !important; }
    div[data-testid="stTextInput"] { width: 150px !important; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'abs_list' not in st.session_state: st.session_state.abs_list = []
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    sidebar_limit = st.number_input("Mostrar hasta ID:", min_value=1, max_value=21, value=14)
    
    st.write("---")
    st.markdown("## ✅Asistencia/Comida🍱")
    if st.button("⌨️ MODO MANUAL" if not st.session_state.manual_mode else "🌐 MODO AUTO"):
        st.session_state.manual_mode = not st.session_state.manual_mode
        st.rerun()
    
    active_ids = []
    st.write("---")
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown("**ID**")
    c2.markdown("**On**")
    c3.markdown("🍴")

    for sid in ALL_IDS:
        if sid <= sidebar_limit:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1: st.markdown(f"**Surtidor {sid}**")
            with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
            with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
            if on and not meal: active_ids.append(sid)

    st.write("---")
    btn_label = "👁️ OCULTAR TURNOS" if st.session_state.show_turns else "🚀 GENERAR TURNOS"
    if st.button(btn_label):
        st.session_state.show_turns = not st.session_state.show_turns
        st.rerun()

    if st.session_state.show_turns and st.session_state.scores and active_ids:
        st.markdown("### ⏭️ Turnos")
        temp_scores = st.session_state.scores.copy()
        simulated_turns = []
        for _ in range(20):
            valid_cands = {k: v for k, v in temp_scores.items() if k in active_ids}
            if not valid_cands: break
            next_p = min(valid_cands, key=valid_cands.get)
            simulated_turns.append(next_p)
            temp_scores[next_p] += 1
        st.markdown("".join([f'<span class="turn-pill">S{t}</span>' for t in simulated_turns]), unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    abs_data = []
    
    def clean_val(v):
        try:
            val_str = str(v).strip().replace(',', '')
            return int(float(val_str)) if val_str not in ["", "-", "nan"] else 0
        except: return 0

    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
        rows, cols = df_raw.shape
        temp_abs = {sid: [] for sid in range(1, sidebar_limit + 1)}

        for r in range(rows):
            for c in range(cols):
                cell_val = str(df_raw.iloc[r, c]).strip()
                if cell_val.isdigit():
                    sid = int(cell_val)
                    if sid in ALL_IDS:
                        p_val = clean_val(df_raw.iloc[r, c + 2]) if c+2 < cols else 0
                        i_val = clean_val(df_raw.iloc[r, c + 3]) if c+3 < cols else 0
                        data_p[sid] = data_p.get(sid, 0) + p_val
                        data_i[sid] = data_i.get(sid, 0) + i_val
                        
                        if sid <= sidebar_limit and p_val == 0:
                            date_val = str(df_raw.iloc[r, 5]).strip() if cols > 5 else "Fecha N/A"
                            temp_abs[sid].append(date_val)
                            
        for sid, dates in temp_abs.items():
            abs_data.append({"Surtidor": f"Surtidor {sid}", "ID": sid, "Count":
