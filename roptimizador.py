import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
ALL_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]

PRIORITY_NAMES = {
    1: "Local Urgente (1)", 2: "Local Urgente (2)",
    3: "Apodaca", 4: "Guadalupe", 5: "Santa Catarina",
    6: "Solidaridad", 7: "Unidad", 8: "Sur Foráneo", 9: "Sur",
    10: "Foráneo Urgente", 11: "Foráneo", 12: "Torreón",
    14: "Saltillo", 16: "Local Desp. Corte",
    17: "Foráneo Urg. Desp. Corte", 18: "Foráneo Desp. Corte", 19: "Torreón Desp. Corte"
}

def get_live_priority(p_val):
    now = datetime.now().time()
    d1245 = datetime.strptime("12:45", "%H:%M").time()
    d1500 = datetime.strptime("15:00", "%H:%M").time()
    d1600 = datetime.strptime("16:00", "%H:%M").time()
    if p_val in [14, 8, 1, 2]: return p_val
    if (3 <= p_val <= 7 or p_val == 9) and now >= d1245: return 16
    if (p_val == 10 or p_val == 11) and now >= d1500: return 18
    if p_val == 12 and now >= d1600: return 19
    if 3 <= p_val <= 9: return 3
    return p_val

def parse_pending(raw_text):
    if not raw_text: return []
    lines = raw_text.strip().split('\n')
    orders = []
    for line in lines:
        if "#N/A" in line or "CANCELADO" in line: continue
        match = re.search(r"(64\d{4})\s+(\d{1,2})\s+(\d+)", line)
        if not match: match = re.search(r"(64\d{4})(\d{1,2})(\d+)", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            if p_int not in PRIORITY_NAMES and len(p_raw) == 2:
                p_int = int(p_raw[0])
                items = p_raw[1] + items
            if p_int in PRIORITY_NAMES:
                orders.append({"ID": oid, "P_Real": get_live_priority(p_int), "Piezas": int(items), "Nombre": PRIORITY_NAMES.get(p_int)})
    return sorted(orders, key=lambda x: (x['P_Real'], -x['Piezas']))

# --- UI STYLE (Industrial Palette: Gray, White, Red) ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F2F2F2; color: #333333; }
    [data-testid="stSidebar"] { background-color: #1E1E1E; color: #F2F2F2; }
    .assignment-card { 
        background: #FFFFFF; padding: 18px; border-left: 10px solid #C0392B; 
        border-radius: 2px; margin-bottom: 12px; border-bottom: 2px solid #DCDCDC;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #C0392B !important; color: white !important; border-radius: 4px; border: none; }
    .stCheckbox { margin-top: 10px; }
    h1, h2, h3 { color: #1E1E1E; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

# Persistent Session Logic
if 'skip_map' not in st.session_state: st.session_state.skip_map = {}

st.title("📦 Panel de Control de Surtido")

# --- SIDEBAR (SPANISH INTERFACE) ---
with st.sidebar:
    st.header("Disponibilidad")
    if st.button("LIMPIAR DATOS"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.write("---")
    active_ids = []
    pardon_ids = []
    for i in ALL_
