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
        background-color: #F8F9FA; 
    }}
    h1, h2, h3, p, span, label {{
        color: #212529 !important; 
    }}
    /* Barra lateral */
    [data-testid="stSidebar"] {{
        background-color: #343A40; 
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    /* Botón de Procesar con letras blancas y negrita */
    .stButton>button {{
        background-color: #990000 !important; 
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px;
        border: none;
        width: 100%;
        height: 3em;
        font-size: 18px !important;
    }}
    .stButton>button:hover {{
        background-color: #CC0000 !important;
        color: white !important;
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
        
        total_counts = {}
        for id_ in active_selection:
            total_counts[id_] = hist_counts.get(id_, 0) + curr_counts.get(id_, 0
