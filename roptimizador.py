import streamlit as st
import re
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
# The GID for the "PRODUCTIVIDAD SURTIDO" tab inside your daily links.
# If you don't know it, check the URL when you are ON that tab.
DAILY_TAB_GID = "0" # Change this if the tab is not the first one (GID 0)

MONTH_GIDS = {
    "ABRIL 2026": "2083245391",
}
BASE_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid="

# --- 2. UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #17202A; }
    h1, h2, h3, p, span, label { color: white !important; font-family: Arial; }
    div.stButton > button { 
        background-color: #C0392B !important; 
        color: white !important; 
        font-weight: bold !important;
        border: 2px solid white;
    }
    [data-testid="stSidebar"] { background-color: #111821 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("📅 Configuración")
    sel_month = st.selectbox("Mes:", ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"], index=3)
    sel_year = st.selectbox("Año:", [2025, 2026, 2027], index=1)
    limit = st.number_input("Surtidores a procesar:", 1, 21, 14)
    
    lookup_key = f"{sel_month} {sel_year}"
    MASTER_SHEET_URL = f"{BASE_URL}{MONTH_GIDS.get(lookup_key, '2083245391')}"

# --- 4. THE BRAIN (AUTO-SCRAPER) ---
st.title(f"🚀 Procesando: {lookup_key}")

if st.button("✳️ EXTRAER DATOS DE TODOS LOS LINKS"):
    try:
        # Step 1: Get the list of links from RELLENO_LINKS
        master_df = pd.read_csv(MASTER_SHEET_URL)
        
        totals_p = {i: 0 for i in range(1, limit + 1)}
        totals_i = {i: 0 for i in range(1, limit + 1)}
        abs_dates = {i: [] for i in range(1, limit + 1)}

        progress_bar = st.progress(0)
        status_text = st.empty()

        # Step 2: Loop through each link
        for index, row in master_df.iterrows():
            fecha = str(row.iloc[0])
            url_raw = str(row.iloc[1])
            
            status_text.text(f"Leyendo: {fecha}...")
            
            # Transform URL to export the specific tab "PRODUCTIVIDAD SURTIDO"
            # We look for a GID in the link you pasted, or use the DAILY_TAB_GID
            if "/edit" in url_raw:
                # If the pasted link already has a GID, we use it. Otherwise, we force GID 0.
                gid_match = re.search(r"gid=(\d+)", url_raw)
                target_gid = gid_match.group(1) if gid_match else DAILY_TAB_GID
                csv_url = url_raw.split('/edit')[0] + f"/export?format=csv&gid={target_gid}"
            else:
                continue

            try:
                # Step 3: Fetch and Parse the daily table
                day_df = pd.read_csv(csv_url)
                
                for sid in range(1, limit + 1):
                    # We search Column B (index 1) for the ID
                    match = day_df[day_df.iloc[:, 1].astype(str) == str(sid)]
                    
                    if not match.empty:
                        # Column D (index 3) = Pedidos, Column F (index 5) = Piezas
                        p = pd.to_numeric(str(match.iloc[0, 3]).replace('.',''), errors='coerce') or 0
                        i = pd.to_numeric(str(match.iloc[0, 5]).replace('.',''), errors='coerce') or 0
                        
                        totals_p[sid] += p
                        totals_i[sid] += i
                        if p == 0: abs_dates[sid].append(fecha)
            except Exception:
                continue
            
            progress_bar.progress((index + 1) / len(master_df))

        # Step 4: Final formatting
        st.session_state.results = [
            {"Surtidor": f"Surtidor {s}", "Pedidos": int(totals_p[s]), "Piezas": int(totals_i[s]), 
             "Ausencias": len(abs_dates[s]), "Fechas": ", ".join(abs_dates[s])}
            for s in range(1, limit + 1)
        ]
        status_text.text("✅ ¡Proceso completado!")
        st.rerun()

    except Exception as e:
        st.error(f"Error Crítico: {e}")

# --- 5. DISPLAY ---
if 'results' in st.session_state:
    df_final = pd.DataFrame(st.session_state.results)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏅 Ranking del Mes")
        st.dataframe(df_final.sort_values("Pedidos", ascending=False)[["Surtidor", "Pedidos", "Piezas"]], hide_index=True, use_container_width=True)
    
    with c2:
        st.subheader("⚠️ Historial de Ausencias")
        st.dataframe(df_final[df_final["Ausencias"] > 0][["Surtidor", "Ausencias", "Fechas"]], hide_index=True, use_container_width=True)
    
    st.download_button("📥 Descargar Reporte CSV", df_final.to_csv(index=False), f"Productividad_{lookup_key}.csv")
