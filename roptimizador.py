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

# --- ESTILO PERSONALIZADO (ROJO CEREZA, GRIS, NEGRO) ---
st.set_page_config(page_title="Optimizador de Pedidos", layout="wide")

st.markdown(f"""
    <style>
    /* Fondo general y textos */
    .stApp {{
        background-color: #F8F9FA; /* Gris muy claro */
    }}
    h1, h2, h3, p, span, label {{
        color: #212529 !important; /* Gris oscuro / Negro */
    }}
    /* Barra lateral */
    [data-testid="stSidebar"] {{
        background-color: #343A40; /* Gris oscuro */
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    /* Botones */
    .stButton>button {{
        background-color: #990000; /* Rojo Cereza */
        color: white;
        border-radius: 5px;
        border: none;
        width: 100%;
    }}
    .stButton>button:hover {{
        background-color: #CC0000;
        color: white;
    }}
    /* Cajas de texto */
    textarea {{
        background-color: #FFFFFF !important;
        border: 1px solid #CED4DA !important;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("📦 Optimizador de Despacho de Pedidos")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Configuración")
    if st.button("🔄 Reiniciar Aplicación"):
        st.rerun()
    
    st.write("---")
    st.write("**Personal Activo**")
    st.caption("Desmarca a quienes estén en lunch o no estén trabajando.")
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
    procesar = st.button("🚀 Procesar Turnos")

if procesar:
    if current_input:
        hist_counts = parse_data(hist_input, active_selection)
        curr_counts = parse_data(current_input, active_selection)
        
        # Combinar conteos para justicia total
        total_counts = {}
        for id_ in active_selection:
            total_counts[id_] = hist_counts.get(id_, 0) + curr_counts.get(id_, 0)
        
        st.markdown('<div style="padding:10px; border-radius:5px; background-color:#D4EDDA; color:#155724; border:1px solid #C3E6CB;">✅ Información absorbida y procesada correctamente.</div>', unsafe_allow_html=True)
        
        st.subheader("Próximos 10 Turnos:")
        temp_total = total_counts.copy()
        
        # Generar lista de 10 turnos uno debajo de otro
        for i in range(10):
            # Lógica de equidad: el que tiene menos total va primero
            next_up = min(temp_total, key=temp_total.get)
            temp_total[next_up] += 1
            
            if i == 0:
                # El primero en rojo cereza y más grande
                st.markdown(f"<p style='font-size:24px; color:#990000; font-weight:bold; margin:0;'>• TURNO 1: ID {next_up}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='font-size:18px; color:#343A40; margin:0;'>• Turno {i+1}: ID {next_up}</p>", unsafe_allow_html=True)
    else:
        st.error("Por favor, pega la tabla actual antes de procesar.")
else:
    st.info("Esperando datos para calcular los siguientes turnos...")
