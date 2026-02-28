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

# --- UI STYLE (Industrial: Conch White, Charcoal, Firebrick Red) ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #E8E8E8; color: #2D2D2D; }
    [data-testid="stSidebar"] { background-color: #1A1A1A; color: #E8E8E8; }
    .assignment-card { 
        background: #FFFFFF; padding: 16px; border-left: 10px solid #B03A2E; 
        border-radius: 2px; margin-bottom: 10px; border-bottom: 1px solid #CCCCCC;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button { background-color: #B03A2E !important; color: white !important; border-radius: 4px; }
    .skip-btn-style { background-color: #4A4A4A !important; font-size: 0.8em !important; }
    h1, h2, h3 { color: #1A1A1A; font-family: 'Helvetica', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# Persistent State
if 'skip_map' not in st.session_state: st.session_state.skip_map = {}
if 'pedidos' not in st.session_state: st.session_state.pedidos = []
if 'scores' not in st.session_state: st.session_state.scores = {}

st.title("📦 Panel de Control de Surtido")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Disponibilidad")
    if st.button("LIMPIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    st.write("---")
    active_ids = []
    pardon_ids = []
    for i in ALL_IDS:
        c1, c2, c3 = st.columns([2,1,1])
        with c1: on = st.toggle(f"Surtidor {i}", value=True, key=f"on_{i}")
        with c2: meal = st.toggle("🍴", key=f"m_{i}")
        with c3: pdr = st.checkbox("OVR", key=f"p_{i}")
        if on and not meal: active_ids.append(i)
        if pdr: pardon_ids.append(i)

# --- DATA INPUTS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("1. Histórico", height=100)
with col2: t_in = st.text_area("2. Totales de Hoy", height=100)
with col3: o_in = st.text_area("3. Nuevos Pedidos", height=100)

if st.button("CALCULAR ROTACIÓN"):
    if not o_in: st.error("Sin datos en columna 3.")
    else:
        pat = r"(\d+)[A-Z\s\.]+(\d+)"
        h_blocks = []
        for line in h_in.strip().split('\n'):
            m = re.findall(pat, line)
            if m: h_blocks.append({int(k): int(v) for k, v in m})
        t_m = re.findall(pat, t_in)
        t_counts = {int(k): int(v) for k, v in t_m if int(k) in active_ids}
        st.session_state.pedidos = parse_pending(o_in)
        
        scores = {}
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        avg = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        top = 0
        for idx in active_ids:
            is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            scores[idx] = (int(avg / len(ALL_IDS)) if (idx in pardon_ids or is_new) else h_sum) + t_counts.get(idx, 0)
            top = max(top, scores[idx])
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids: scores[idx] = top + 5
        st.session_state.scores = scores

# --- QUEUE DISPLAY ---
if st.session_state.pedidos:
    st.write("---")
    st.subheader(f"Pedidos en Cola ({datetime.now().strftime('%H:%M')})")
    
    current_scores = st.session_state.scores.copy()
    last_id = None

    for i, p in enumerate(st.session_state.pedidos[:50]):
        skips = st.session_state.skip_map.get(p['ID'], 0)
        rotation = sorted(current_scores.items(), key=lambda x: x[1])
        
        if not rotation: break
        
        target_idx = min(skips, len(rotation) - 1)
        assigned_id = rotation[target_idx][0]
        
        # Avoid back-to-back if no skips active
        if assigned_id == last_id and len(rotation) > 1 and target_idx == 0:
            assigned_id = rotation[1][0]

        current_scores[assigned_id] += 1
        last_id = assigned_id

        c_check, c_body, c_skip = st.columns([1, 12, 4])
        with c_check:
            is_done = st.checkbox("", key=f"done_{p['ID']}_{i}")
        if not is_done:
            with c_body:
                st.markdown(f"""<div class="assignment-card">
                    <span style="color:#B03A2E; font-weight:bold; font-size:1.1em;">ID {assigned_id}</span> ⮕ 
                    <b>{p['ID']}</b> | {p['Nombre']} | {p['Piezas']} Pzs</div>""", unsafe_allow_html=True)
            with c_skip:
                if st.button("SIGUIENTE MEJOR", key=f"sk_{p['ID']}_{i}"):
                    st.session_state.skip_map[p['ID']] = skips + 1
                    st.rerun()
