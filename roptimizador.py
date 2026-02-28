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
        
        # Ignore orders that already have extra data (Assigned ID / Picker Name)
        parts = re.split(r'\s{2,}', line)
        if len(parts) > 4: continue

        match = re.search(r"(64\d{4})\s+(\d{1,2})\s+(\d+)", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            if p_int in PRIORITY_NAMES:
                orders.append({
                    "ID": oid, 
                    "P_Real": get_live_priority(p_int), 
                    "Piezas": int(items), 
                    "Nombre": PRIORITY_NAMES.get(p_int)
                })
    return sorted(orders, key=lambda x: (x['P_Real'], -x['Piezas']))

# --- UI STYLE (Industrial High-Contrast & Optimized Spacing) ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #EAECEE; color: #1C2833; }
    
    /* Sidebar: High Contrast White Text on Dark Background */
    [data-testid="stSidebar"] { 
        background-color: #17202A !important; 
    }
    
    /* Force Sidebar labels, headers, and text to White */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown { 
        color: #FFFFFF !important; 
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }

    /* Spacing for Surtidores: Balanced Density */
    [data-testid="stSidebar"]
