import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN Y MAPA DE PRIORIDADES ---
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
        if not match:
            match = re.search(r"(64\d{4})(\d{1,2})(\d+)", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            if p_int not in PRIORITY_NAMES and len(p_raw) == 2:
                p_int = int(p_raw[0])
                items = p_raw[1] + items
            if p_int in PRIORITY_NAMES:
                orders.append({
                    "ID_Pedido": oid, 
                    "P_Real": get_live_priority(p_int), 
                    "Piezas": int(items), 
                    "P_Original": p_int,
                    "Nombre_P": PRIORITY_NAMES.get(p_int)
                })
    return sorted(orders, key=lambda x: (x['P_Real'], -x['Piezas']))

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Optimizador de Almacén", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .assignment-card { 
        background: white; padding: 12px; border-left: 10px solid #990000; 
        border-radius: 6px; margin-bottom: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Rotación Inteligente de Surtido")

# --- BARRA LATERAL: PERSONAL ---
with st.sidebar:
    st.header("Gestión de Equipo")
    if st.button("🔄 REINICIAR TODO"): 
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.write("---")
    active_ids = []
    pardon_ids = []
    for i in ALL_IDS:
        c1, c2, c3 = st.columns([2,1,1])
        with c1: on = st.toggle(f"ID {i}", value=True, key=f"on_{i}")
        with c2: meal = st.toggle("🍴", key=f"m_{i}")
        with c3: pdr = st.checkbox("OVR", key=f"p_{i}", help="Perdón por ausencia/Nuevo")
        if on and not meal: active_ids.append(i)
        if pdr: pardon_ids.append(i)

# --- ENTRADAS DE DATOS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("1. Histórico (Días anteriores)", height=150)
with col2: t_in = st.text_area("2. Totales de Hoy", height=150)
with col3: o_in = st.text_area("3. Pedidos Pendientes (Pegar aquí)", height=150)

if st.button("💊 GENERAR ASIGNACIONES"):
    if not o_in:
        st.error("Por favor, pega los pedidos en la columna 3.")
    else:
        # Lógica de Rotación
        pat = r"(\d+)[A-Z\s\.]+(\d+)"
        h_blocks = []
        for line in h_in.strip().split('\n'):
            m = re.findall(pat, line)
            if m: h_blocks.append({int(k): int(v) for k, v in m})
        
        t_m = re.findall(pat, t_in)
        t_counts = {int(k): int(v) for k, v in t_m if int(k) in active_ids}
        
        st.session_state.pedidos_procesados = parse_pending(o_in)

        scores = {}
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        avg = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        top = 0
        
        for idx in active_ids:
            is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            if idx in pardon_ids or is_new:
                scores[idx] = int(avg / len(ALL_IDS)) + t_counts.get(idx, 0) if avg > 0 else t_counts.get(idx, 0)
            else:
                scores[idx] = h_sum + t_counts.get(idx, 0)
                top = max(top, scores[idx])
        
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids: scores[idx] = top + 5
            
        st.session_state.puntuaciones = scores

# --- MOSTRAR RESULTADOS (PERSISTENTES) ---
if 'pedidos_procesados' in st.session_state:
    st.write("---")
    st.subheader(f"Cola de Asignación Actual ({datetime.now().strftime('%H:%M')})")
    
    scores_temp = st.session_state.puntuaciones.copy()
    last_id = None
    
    for i, pedido in enumerate(st.session_state.pedidos_procesados[:40]):
        # Calcular quién sigue
        rotacion = sorted(scores_temp.items(), key=lambda x: x[1])
        if not rotacion: break
        best_id = rotacion[0][0]
        if best_id == last_id and len(rotacion) > 1:
            best_id = rotacion[1][0]
        
        scores_temp[best_id] += 1
        last_id = best_id
        
        # UI de la Tarjeta
        c_chk, c_crd = st.columns([1, 20])
        with c_chk: 
            # El estado de "Listo" se guarda por ID de pedido
            completado = st.checkbox("", key=f"done_{pedido['ID_Pedido']}_{i}")
        
        if not completado:
            with c_crd:
                st.markdown(f"""
                <div class="assignment-card">
                    <b style="color:#990000; font-size:20px;">SURTIDOR ID: {best_id}</b> ⮕ 
                    <b>Pedido: {pedido['ID_Pedido']}</b> | {pedido['Nombre_P']} | {pedido['Piezas']} Piezas
                </div>
                """, unsafe_allow_html=True)

st.write("---")
st.caption("Cortes Automáticos: Locales 12:45 | Foráneos 15:00 | Torreón 16:00")
