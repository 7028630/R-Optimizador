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

# --- UI STYLE ---
st.set_page_config(page_title="Surtido Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #EAECEE; color: #1C2833; }
    [data-testid="stSidebar"] { background-color: #17202A !important; min-width: 400px !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] svg { fill: #FFFFFF !important; width: 18px !important; height: 18px !important; }
    
    /* Toggle Visibility Fix */
    div[data-testid="stWidgetLabel"] + div div[role="switch"] { background-color: #BDC347 !important; border: 2px solid #ECF0F1 !important; }
    div[data-testid="stWidgetLabel"] + div div[role="switch"][aria-checked="true"] { background-color: #E74C3C !important; }

    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div { margin-bottom: -12px !important; }

    .id-badge { background-color: #17202A; color: #FFFFFF !important; padding: 8px 16px; border-radius: 4px; font-weight: 900; font-size: 1.3em; margin-right: 20px; border: 1px solid #566573; }
    .assignment-card { background: #FFFFFF; padding: 15px; border-left: 12px solid #C0392B; border-radius: 4px; margin-bottom: 8px; border-bottom: 2px solid #AEB6BF; color: #17202A; display: flex; align-items: center; }
    div.stButton > button { background-color: #C0392B !important; color: white !important; border-radius: 50px !important; padding: 10px 24px !important; font-weight: 900 !important; width: 100% !important; border: none !important; }
    
    /* Next Turns Styling */
    .turn-pill { background: #2E4053; color: white; padding: 4px 10px; border-radius: 20px; margin: 2px; display: inline-block; font-size: 0.8em; border: 1px solid #566573; }
    </style>
""", unsafe_allow_html=True)

if 'skip_map' not in st.session_state: st.session_state.skip_map = {}
if 'pedidos' not in st.session_state: st.session_state.pedidos = []
if 'scores' not in st.session_state: st.session_state.scores = {}

st.title("📦 Panel de Control de Surtido")

# --- SIDEBAR ---
with st.sidebar:
    # 1. CLEAN BUTTON AT TOP
    if st.button("🗑️ LIMPIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    st.header("Disponibilidad")
    st.write("---")
    h1, h2, h3 = st.columns([2,1,1])
    with h1: st.write("**Surtidor**")
    with h2: st.write("**🍴**")
    with h3: st.write("**Excepción**")
    
    active_ids = []
    pardon_ids = []
    for i in ALL_IDS:
        c_n, c_m, c_e = st.columns([2,1,1])
        with c_n: on = st.toggle(f"ID {i}", value=True, key=f"on_{i}")
        with c_m: meal = st.toggle("", key=f"m_{i}", help="Personal en horario de comida")
        with c_e: pdr = st.checkbox("", key=f"p_{i}")
        if on and not meal: active_ids.append(i)
        if pdr: pardon_ids.append(i)

    # 2. NEXT 10 TURNS SECTION
    st.write("---")
    st.subheader("🔄 Próximos 10 Turnos")
    if not st.session_state.scores:
        st.info("Procesa datos para ver turnos.")
    else:
        temp_scores = st.session_state.scores.copy()
        next_turns = []
        for _ in range(10):
            # Sort by current simulated score
            valid_rotation = {k: v for k, v in temp_scores.items() if k in active_ids}
            if not valid_rotation: break
            nxt_id = min(valid_rotation, key=valid_rotation.get)
            next_turns.append(nxt_id)
            temp_scores[nxt_id] += 1
        
        # Display as pills
        turn_html = "".join([f'<span class="turn-pill">ID {tid}</span>' for tid in next_turns])
        st.markdown(turn_html, unsafe_allow_html=True)

# --- INPUT AREAS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("1. Histórico", height=80)
with col2: t_in = st.text_area("2. Totales de Hoy", height=80)
with col3: o_in = st.text_area("3. Nuevos Pedidos", height=120)

if st.button("💊 PROCESAR TURNOS"):
    if not o_in: st.error("No hay datos.")
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
        st.rerun()

# --- QUEUE DISPLAY ---
if st.session_state.pedidos:
    st.write("---")
    st.subheader(f"Cola de Trabajo Actual ({datetime.now().strftime('%H:%M')})")
    current_scores = st.session_state.scores.copy()
    last_id = None
    for i, p in enumerate(st.session_state.pedidos[:50]):
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
        with c_chk: done = st.checkbox("", key=f"d_{p['ID']}_{i}")
        if not done:
            with c_crd:
                st.markdown(f'<div class="assignment-card"><span class="id-badge">ID {assigned_id}</span><span><b>{p["ID"]}</b> | {p["Nombre"]} | {p["Piezas"]} Pzs</span></div>', unsafe_allow_html=True)
            with c_nxt:
                if st.button("SIGUIENTE MEJOR", key=f"sk_{p['ID']}_{i}"):
                    st.session_state.skip_map[p['ID']] = skips + 1
                    st.rerun()
