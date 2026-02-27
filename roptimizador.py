import streamlit as st
import re

# Configuración de IDs posibles
ALL_IDS = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12]

def parse_data(raw_text, active_ids):
    if not raw_text:
        return {}
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    data = re.findall(pattern, raw_text)
    return {int(id_): int(orders) for id_, orders in data if int(id_) in active_ids}

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
        border: 1px solid #6c757d !important;
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
    st.write("**Personal Activo**")
    st.caption("Desmarca a quienes estén en hora de comida o estén ausentes.")
    active_selection = []
    for id_num in ALL_IDS:
        if st.checkbox(f"ID {id_num}", value=True):
            active_selection.append(id_num)

# --- CUERPO PRINCIPAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Datos Históricos")
    hist_input = st.text_area("Pega aquí las tablas de días anteriores:", height=300, placeholder="Pega el contenido aquí...")

with col2:
    st.subheader("2. Estado Actual")
    current_input = st.text_area("Pega aquí la tabla MÁS RECIENTE:", height=300, placeholder="Pega el contenido aquí...")
    procesar = st.button("💊 PROCESAR TURNOS")

if procesar:
    if current_input:
        hist_counts = parse_data(hist_input, active_selection)
        curr_counts = parse_data(current_input, active_selection)
        
        # --- NUEVA LÓGICA DE ASISTENCIA ---
        total_counts = {}
        
        # Encontrar el valor máximo de órdenes entre los que SÍ vinieron (para el castigo)
        max_orders_present = 0
        for id_ in active_selection:
            h = hist_counts.get(id_, 0)
            c = curr_counts.get(id_, 0)
            if h > 0: # Si tiene historial, es un cumplido
                max_orders_present = max(max_orders_present, h + c)
        
        # Si nadie vino antes, usamos un valor base alto
        penalty_value = max_orders_present if max_orders_present > 0 else 100

        for id_ in active_selection:
            h = hist_counts.get(id_, 0)
            c = curr_counts.get(id_, 0)
            
            if h == 0 and c == 0:
                # Es alguien que no ha trabajado nada: se le pone al final (penalizado)
                total_counts[id_] = penalty_value + 10 
            else:
                # Es alguien que ha estado trabajando: se usa su total real
                total_counts[id_] = h + c

        st.markdown('<div style="padding:10px; border-radius:5px; background-color:#D4EDDA; color:#155724; border:1px solid #C3E6CB;">✅ Lógica de Asistencia: Priorizando a los cumplidos. Los que faltaron irán al final hasta que el grupo los alcance.</div>', unsafe_allow_html=True)
        
        st.subheader("Próximos 10 Turnos:")
        temp_total = total_counts.copy()
        last_id = None
        
        for i in range(10):
            if not temp_total: break
            
            candidates = sorted(temp_total.items(), key=lambda x: x[1])
            next_up = candidates[0][0]
            
            # Regla de no repetición inmediata
            if next_up == last_id and len(candidates) > 1:
                next_up = candidates[1][0]
            
            temp_total[next_up] += 1
            last_id = next_up
            
            color = "#990000" if i == 0 else "#343A40"
            size = "26px" if i == 0 else "18px"
            weight = "bold" if i == 0 else "normal"
            
            st.markdown(f"<p style='font-size:{size}; color:{color}; font-weight:{weight}; margin:5px 0;'>• Turno {i+1}: ID {next_up}</p>", unsafe_allow_html=True)
    else:
        st.error("Por favor, pega la tabla actual antes de procesar.")
else:
    st.info("Esperando datos para calcular los siguientes turnos...")
