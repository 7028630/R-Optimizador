import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important; color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; }
    [data-testid="stSidebar"] { background-color: #111821 !important; min-width: 320px !important; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; }
    .stats-container { background-color: #212F3C; padding: 15px; border-radius: 10px; border: 1px solid #C0392B; text-align: center; margin-top: -20px; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}

# --- SIDEBAR: ASISTENCIA ---
with st.sidebar:
    st.markdown("## ✅ Asistencia / Comida 🍴")
    if st.button("🔄 REINICIAR TODO"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    active_ids = []
    st.write("---")
    for sid in ALL_IDS:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.markdown(f"**S{sid}**")
        with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        if on and not meal: active_ids.append(sid)

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad Surtido")

c1, c2 = st.columns([1, 1])
with c1:
    st.info("📊 **Modo Historial:** Escaneando bloques de datos en Google Sheets...")
with c2:
    t_in = st.text_area("2. Datos Live (Hoy)", height=150, placeholder="Pega aquí los datos del sistema de hoy...")

if st.button("✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}

    def clean_val(v):
        if pd.isna(v) or v == "" or "-" in str(v): return 0
        s = re.sub(r'[^\d]', '', str(v)) # Remove commas, dots, or symbols
        return int(s) if s.isdigit() else 0

    # 1. SCAN GOOGLE SHEET FOR ALL DATA BLOCKS
    try:
        # Load the sheet without assuming a header because of the complex layout
        df_raw = pd.read_csv(SHEET_URL, header=None)
        
        # Iterate through every cell to find "No." or IDs
        for r in range(len(df_raw)):
            for c in range(len(df_raw.columns)):
                val = str(df_raw.iloc[r, c]).strip()
                
                # Check if this cell is a valid ID (1-21)
                if val.isdigit() and int(val) in ALL_IDS:
                    sid = int(val)
                    # Based on your image: Pedidos is 2 columns to the right, Piezas is 3 columns to the right
                    try:
                        ped = clean_val(df_raw.iloc[r, c + 2])
                        pza = clean_val(df_raw.iloc[r, c + 3])
                        data_p[sid] = data_p.get(sid, 0) + ped
                        data_i[sid] = data_i.get(sid, 0) + pza
                    except:
                        continue
    except Exception as e:
        st.error(f"Error procesando el formato de la hoja: {e}")

    # 2. PROCESS LIVE INPUT (REGEX)
    if t_in.strip():
        pat = r"(\d+)\s+.*?\s+([\d\.,]+)\s+([\d\.,\-]+)"
        matches = re.findall(pat, t_in)
        for sid_raw, ped, pza in matches:
            sid = int(sid_raw)
            data_p[sid] = data_p.get(sid, 0) + clean_val(ped)
            data_i[sid] = data_i.get(sid, 0) + clean_val(pza)

    # 3. BUILD RANKING
    combined = []
    for sid in set(list(data_p.keys()) + list(data_i.keys())):
        combined.append({
            "ID": sid,
            "Surtidor": f"Surtidor {sid}",
            "Pedidos": data_p.get(sid, 0),
            "Piezas": data_i.get(sid, 0)
        })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {sid: data_p.get(sid, 0) for sid in ALL_IDS}
    st.rerun()

# --- VISUALS ---
if st.session_state.final_ranking:
    df = pd.DataFrame(st.session_state.final_ranking)
    col_chart, col_table = st.columns([1.2, 0.8])
    
    with col_chart:
        fig = px.pie(df, values='Pedidos', names='Surtidor', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

        stdev_val = df['Pedidos'].std()
        st.markdown(f'<div class="stats-container">Desviación Estándar (Balance): <b>{stdev_val:.2f}</b></div>', unsafe_allow_html=True)

    with col_table:
        st.markdown("### 🏆 Ranking Acumulado")
        st.table(df[["Surtidor", "Pedidos", "Piezas"]])
