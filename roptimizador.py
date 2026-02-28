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
        if "#N/A" in line or "CANCELADO" in line: continue
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

# --- UI STYLE (Industrial High-Contrast) ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #EAECEE; color: #1C2833; }
    
    /* Sidebar Text Correction - Force White */
    [data-testid="stSidebar"] { 
        background-color: #17202A !important; 
    }
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2 { 
        color: #FFFFFF !important; 
        font-weight: bold !important;
    }

    /* Target ID Badge: White on Dark */
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

    /* Cards */
    .assignment-card { 
        background: #FFFFFF; padding: 20px; border-left: 12px solid #922B21; 
        border-radius: 4px; margin-bottom: 12px; border-bottom: 2px solid #AEB6BF;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
        color: #17202A;
        display: flex; align-items: center;
    }
    
    /* Process Pill Button */
    div.stButton > button {
        background-color: #922B21 !important;
        color: white !important;
        border-radius: 50px !important; 
        padding: 10px 24px !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    
    /* Next Best Button */
    .skip-btn-container div.stButton > button {
        background-color: #2E4053 !important;
        font-size: 0.8em !important;
        border-radius: 20px !important;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- INPUT AREAS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("1. Histórico", height=100)
with col2: t_in = st.text_area("2. Totales de Hoy", height=100)
with col3: o_in = st.text_area("3. Nuevos Pedidos", height=100)

if st.button("💊 PROCESAR TURNOS"):
    if not o_in: st.error("No hay datos detectados.")
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
    st.subheader(f"Cola de Trabajo Actual ({datetime.now().strftime('%H:%M')})")
    current_scores = st.session_state.scores.copy()
    last_id = None

    for i, p in enumerate(st.session_state.pedidos[:45]):
        skips = st.session_state.skip_map.get(p['ID'], 0)
        rotation = sorted(current_scores.items(), key=lambda x: x[1])
        if not rotation: break
        
        target_idx = min(skips, len(rotation) - 1)
        assigned_id = rotation[target_idx][0]
        
        if assigned_id == last_id and len(rotation) > 1 and target_idx == 0:
            assigned_id = rotation[1][0]

        current_scores[assigned_id] += 1
        last_id = assigned_id

        c_chk, c_crd, c_nxt = st.columns([1, 14, 4])
        with c_chk:
            done = st.checkbox("", key=f"d_{p['ID']}_{i}")
        if not done:
            with c_crd:
                st.markdown(f"""<div class="assignment-card">
                    <span class="id-badge">ID {assigned_id}</span>
                    <span><b>{p['ID']}</b> | {p['Nombre']} | {p['Piezas']} Pzs</span>
                    </div>""", unsafe_allow_html=True)
            with c_nxt:
                st.markdown('<div class="skip-btn-container">', unsafe_allow_html=True)
                if st.button("SIGUIENTE MEJOR", key=f"sk_{p['ID']}_{i}"):
                    st.session_state.skip_map[p['ID']] = skips + 1
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
