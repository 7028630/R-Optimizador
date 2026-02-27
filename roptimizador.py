import streamlit as st
import re

# Configuración de IDs posibles
ALL_IDS = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12]

def parse_data_by_blocks(raw_text):
    if not raw_text:
        return []
    # Separamos por bloques (asumiendo que cada lista histórica es un bloque)
    blocks = raw_text.strip().split('\n')
    parsed_blocks = []
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    for block in blocks:
        data = re.findall(pattern, block)
        if data:
            parsed_blocks.append({int(id_): int(orders) for id_, orders in data})
    return parsed_blocks

# --- ESTILO PERSONALIZADO ---
st.set_page_config(page_title="Optimizador de Pedidos", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #F8F9FA; }}
    button div p {{ color: white !important; font-weight: bold !important; }}
    div.stButton > button {{
        background-color: #990000 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
        width: 100%;
        height: 3em;
    }}
    section[data-testid="stSidebar"] .stButton > button {{
        background-color: #495057 !important;
        color: white !important;
    }}
    [data-testid="stSidebar"] {{ background-color: #343A40; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    </style>
    """, unsafe_allow_html=True)

st.title("📦 Optimizador de Despacho de Pedidos")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    if st.button("🔄 BORRAR MEMORIA DE DATOS INGRESADOS"):
        st.rerun()
    
    st.write("---")
    st.write("**Estado del Personal**")
    
    active_selection = []
    overrides = []
    
    col_act, col_over = st.columns(2)
    with col_act:
        st.caption("¿Presente?")
        for id_num in ALL_IDS:
            if st.checkbox(f"ID {id_num}", value=True, key=f"act_{id_num}"):
                active_selection.append(id_num)
    
    with col_over:
        st.caption("¿Perdonar?")
        for id_num in ALL_IDS:
            if st.checkbox(f"OVR", value=False, key=f"ovr_{id_num}", help="Anular castigo por faltas"):
                overrides.append(id_num)

# --- CUERPO PRINCIPAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Datos Históricos")
    hist_input = st.text_area("Pega aquí las tablas de días anteriores (una por línea):", height=300)

with col2:
    st.subheader("2. Estado Actual")
    current_input = st.text_area("Pega aquí la tabla MÁS RECIENTE:", height=300)
    procesar = st.button("💊 PROCESAR TURNOS")

if procesar:
    if current_input:
        blocks = parse_data_by_blocks(hist_input)
        curr_data = re.findall(r"(\d+)[A-Z\s\.]+(\d+)", current_input)
        curr_counts = {int(id_): int(orders) for id_, orders in curr_data if int(id_) in active_selection}
        
        # Lógica de Ausencia de 3 días
        total_counts = {}
        # Calculamos el promedio de los que sí están trabajando para los "nuevos"
        temp_sums = [sum(b.values()) for b in blocks if b]
        avg_base = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        
        # Valor de castigo (el más alto del equipo)
        max_seen = 0
        
        for id_ in active_selection:
            # Revisar últimos 3 bloques
            recent_activity = [b.get(id_, 0) for b in blocks[-3:]] if len(blocks) >= 3 else [1] # Si no hay historia suficiente, no castigar
            
            has_been_absent = sum(recent_activity) == 0
            h_total = sum(b.get(id_, 0) for b in blocks)
            c_val = curr_counts.get(id_, 0)
            
            if id_ in overrides or has_been_absent:
                # Si es perdonado o es "nuevo" por ausencia de 3 días, entra con el promedio actual
                total_counts[id_] = int(avg_base / len(ALL_IDS)) + c_val if avg_base > 0 else c_val
            else:
                total_counts[id_] = h_total + c_val
                max_seen = max(max_seen, total_counts[id_])

        # Aplicar castigo a los que faltaron pero NO cumplen los 3 días de gracia ni tienen override
        for id_ in total_counts:
            if total_counts[id_] == 0 and id_ not in overrides:
                total_counts[id_] = max_seen + 5

        st.success("✅ Turnos calculados con reglas de asistencia y gracia por 3 días de ausencia.")
        
        st.subheader("Próximos 10 Turnos:")
        temp_total = total_counts.copy()
        last_id = None
        for i in range(10):
            candidates = sorted(temp_total.items(), key=lambda x: x[1])
            next_up = candidates[0][0]
            if next_up == last_id and len(candidates) > 1:
                next_up = candidates[1][0]
            
            temp_total[next_up] += 1
            last_id = next_up
            
            color = "#990000" if i == 0 else "#343A40"
            st.markdown(f"<p style='font-size:18px; color:{color};'>• Turno {i+1}: <b>ID {next_up}</b></p>", unsafe_allow_html=True)
    else:
        st.error("Pega la tabla actual.")
