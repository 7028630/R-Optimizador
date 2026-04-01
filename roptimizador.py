import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- 1. CRITICAL CONFIGURATION ---
# This points directly to your RELLENO_LINKS tab
MONTH_GIDS = {
    "ABRIL 2026": "2083245391",
}
BASE_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid="
ALL_IDS = list(range(1, 22)) 

# --- 2. UI STYLE (FIXED CONTRAST) ---
st.set_page_config(page_title="Productividad Surtido", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    .stApp { background-color: #17202A; }
    /* Fix text and headers to be white */
    h1, h2, h3, p, label, span, th, td { color: #FFFFFF !important; font-family: Arial; }
    
    /* FIX: Button Visibility (Red background, White Bold text) */
    div.stButton > button {
        background-color: #C0392B !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: 2px solid #E74C3C !important;
        width: 100%;
        height: 3em;
    }
    div.stButton > button:hover {
        background-color: #E74C3C !important;
        border: 2px solid #FFFFFF !important;
    }
    
    /* Table Styling */
    .custom-table { width: 100%; border-collapse: collapse; background-color: #212F3C; }
    .custom-table th { background-color: #2C3E50; border-bottom: 2px solid #C0392B; padding: 10px; }
    .custom-table td { border-bottom: 1px solid #34495E; padding: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE INITIALIZATION ---
if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'abs_list' not in st.session_state: st.session_state.abs_list = []

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("## 📅 Periodo")
    sel_month = st.selectbox("Mes:", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=3)
    sel_year = st.selectbox("Año:", [2025, 2026, 2027], index=1)
    lookup_key = f"{sel_month} {sel_year}"
    
    sidebar_limit = st.number_input("Mostrar hasta ID:", min_value=1, max_value=21, value=14)
    SHEET_URL = f"{BASE_URL}{MONTH_GIDS.get(lookup_key, '2083245391')}"

# --- 5. MAIN LOGIC (THE DATA EXTRACTOR) ---
st.title(f"📦 Panel: {lookup_key}")

if st.button("✳️ ACTUALIZAR PANEL"):
    try:
        # Load the sheet - skipping 0 rows because RELLENO_LINKS has a header
        df = pd.read_csv(SHEET_URL)
        
        # Clean numeric columns (G=6, H=7)
        # We force them to strings first to handle dots/commas, then to numbers
        for col_idx in [6, 7]:
            df.iloc[:, col_idx] = df.iloc[:, col_idx].astype(str).str.replace('.', '').str.replace(',', '').replace('nan', '0')
            df.iloc[:, col_idx] = pd.to_numeric(df.iloc[:, col_idx], errors='coerce').fillna(0)

        data_p, data_i, abs_temp = {}, {}, {}

        for _, row in df.iterrows():
            # Regex to find ID in Column B (index 1)
            link_str = str(row.iloc[1])
            match = re.search(r'id=(\d+)', link_str)
            
            if match:
                sid = int(match.group(1))
                if sid <= sidebar_limit:
                    pedidos = int(row.iloc[6])
                    piezas = int(row.iloc[7])
                    fecha = str(row.iloc[0])
                    
                    data_p[sid] = data_p.get(sid, 0) + pedidos
                    data_i[sid] = data_i.get(sid, 0) + piezas
                    
                    if pedidos == 0:
                        if sid not in abs_temp: abs_temp[sid] = []
                        abs_temp[sid].append(fecha)

        # Update Session State
        st.session_state.final_ranking = sorted(
            [{"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)} for s in range(1, sidebar_limit + 1)],
            key=lambda x: x['Pedidos'], reverse=True
        )
        st.session_state.abs_list = [
            {"ID": s, "Surtidor": f"Surtidor {s}", "Count": len(abs_temp.get(s, [])), "Dates": ", ".join(abs_temp.get(s, []))} 
            for s in range(1, sidebar_limit + 1)
        ]
        st.rerun()

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")

# --- 6. DISPLAY ---
if st.session_state.final_ranking:
    df_rank = pd.DataFrame(st.session_state.final_ranking)
    df_active = df_rank[df_rank['Pedidos'] > 0]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🏅 Ranking")
        st.dataframe(df_active[["Surtidor", "Pedidos", "Piezas"]], use_container_width=True, hide_index=True)
    
    with c2:
        st.markdown("### ⚠️ Ausencias")
        df_abs = pd.DataFrame(st.session_state.abs_list)
        st.dataframe(df_abs[df_abs['Count'] > 0][["Surtidor", "Count", "Dates"]], use_container_width=True, hide_index=True)

    # Export Buttons
    st.write("---")
    col_ex1, col_ex2 = st.columns(2)
    col_ex1.download_button("📊 Exportar Ranking", df_rank.to_csv(index=False), "Ranking.csv", "text/csv")
    col_ex2.download_button("❌ Exportar Ausencias", pd.DataFrame(st.session_state.abs_list).to_csv(index=False), "Ausencias.csv", "text/csv")
