import streamlit as st
import re
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
    clean_text = raw_text.replace("a. m.", "am").replace("p. m.", "pm")
    lines = clean_text.strip().split('\n')
    orders = []
    for line in lines:
        line = line.strip()
        if not line or "#N/A" in line or "CANCELADO" in line: continue
        parts = re.split(r'\s{2,}', line)
        if len(parts) > 4: continue 
        match = re.search(r"(64\d{4})\s+(\d{1,2})\s+(\d+)", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            if p_int in PRIORITY_NAMES:
                orders.append({"ID": oid, "P_Real": get_live_priority(p_int), "Piezas": int(items), "Nombre": PRIORITY_NAMES.get(p_int)})
    return sorted(orders, key=lambda x: (x['P_Real'], -x['Piezas']))

# --- UI STYLE: HIGH CONTRAST INDUSTRIAL ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #EAECEE; color: #1C2833; }
    
    /* Sidebar Area */
    [data-testid="stSidebar"] { 
        background-color: #17202A !important; 
        min-width: 380px !important;
    }
    
    /* Global White Text */
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    /* HELP ICON (?) CONTRAST FIX */
    [data-testid="stSidebar"] svg {
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
        filter: drop-shadow(0px 0px 2px rgba(255,255,255,0.5));
    }

    /* TOGGLE TRACK VISIBILITY FIX */
    /* Off State */
    div[role="switch"] {
        background-color: #7B7D7D !important; /* Brighter Gray for visibility */
        border: 2px solid #BDC3C7 !important;
    }
    
    /* On State */
    div[role="switch"][aria-checked="true"] {
        background-color: #C0392B !important; /* Strong Firebrick Red */
        border: 2px solid #E74C3C !important;
    }

    /* Tighter Spacing */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        padding-top: 0px !important;
        padding-bottom: 0px !important;
        margin-bottom: -5px !important;
    }

    /* Card Styling */
    .id-badge {
        background-color: #17202A;
        color: #FFFFFF !important;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 900;
        font-size: 1.3em;
        margin-right: 20px;
        border: 1px solid #566573;
    }

    .assignment-card { 
        background: #FFFFFF; padding: 15px; border-left: 12px
