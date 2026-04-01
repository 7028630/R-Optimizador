import streamlit as st
import re
import pandas as pd

# --- 1. CONFIGURATION ---
# The GID for the "PRODUCTIVIDAD SURTIDO" tab inside your daily links.
# If your template's productivity tab has a different GID, update it here.
DAILY_TAB_GID = "0" 

MONTH_GIDS = {
    "ABRIL 2026": "2083245391",
}
BASE_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid="

# --- 2. UI STYLE (FORCED CONTRAST) ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #17202A; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; font-family: Arial; }
    [data-testid="stSidebar"] { background-color: #111821 !important; }
    
    /* THE BUTTON: Black Bold Text on Bright Red Background */
    div.stButton > button { 
        background-color: #FF0000 !important; 
        color: #000000 !important; 
        font-weight: 900 !important;
        border: 3px solid #FFFFFF !important;
        width: 100%;
        height: 3.5em;
        font-size: 1.2rem !important;
        text-transform: uppercase;
    }
    
    /* Table Styling for Dark Mode */
    .stTable { background-color: #1C2833; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuración")
    sel_month = st.selectbox("Mes Actual:", list(MONTH_GIDS.keys()))
    limit = st.number_input("Surtidores a procesar (IDs):", 1, 21, 14)
    MASTER_URL = f"{BASE_URL}{MONTH_GIDS[sel_month]}"

# --- 4. THE BRAIN (ID-BASED SCRAPER) ---
st.title(f"🚀 Panel de Productividad: {sel_month}")

if st.button("ACTUALIZAR DATOS DE LA LISTA"):
    try:
        # Load the RELLENO_LINKS master list
        master_df = pd.read_csv(MASTER_URL)
        
        # Initialize storage
        totals_p = {i: 0 for i in range(1, limit + 1)}
        totals_i = {i: 0 for i in range(1, limit + 1)}
        abs_dates = {i: [] for i in range(1, limit + 1)}

        progress_bar = st.progress(0)
        status = st.empty()

        for index, row in master_df.iterrows():
            fecha = str(row.iloc[0])
            url_raw = str(row.iloc[1])
            
            if "/edit" in url_raw:
                # Force the specific GID for the "PRODUCTIVIDAD SURTIDO" tab
                csv_url = url_raw.split('/edit')[0] + f"/export?format=csv&gid={DAILY_TAB_GID}"
                
                try:
                    # Read the link's table
                    day_df = pd.read_csv(csv_url)
                    
                    for sid in range(1, limit + 1):
                        # Find ID in Column B (Index 1)
                        # We use .strip() to avoid errors with accidental spaces in the sheet
                        match = day_df[day_df.iloc[:, 1].astype(str).str.strip() == str(sid)]
                        
                        if not match.empty:
                            # Pedidos = Column D (Index 3)
                            # Piezas = Column E (Index 4)
                            p_raw = str(match.iloc[0, 3]).replace('.', '').replace(',', '')
                            i_raw = str(match.iloc[0, 4]).replace('.', '').replace(',', '')
                            
                            p_val = int(float(p_raw)) if p_raw.replace('nan','0').isdigit() else 0
                            i_val = int(float(i_raw)) if i_raw.replace('nan','0').isdigit() else 0
                            
                            totals_p[sid] += p_val
                            totals_i[sid] += i_val
                            if p_val == 0:
                                abs_dates[sid].append(fecha)
                except:
                    continue
            
            progress_bar.progress((index + 1) / len(master_df))
            status.text(f"Procesando: {fecha}")

        # Final Formatting
        st.session_state.results = [
            {"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": totals_p[s], "Piezas": totals_i[s], 
             "Ausencias": len(abs_dates[s]), "Fechas": ", ".join(abs_dates[s])}
            for s in range(1, limit + 1)
        ]
        status.success("¡Datos actualizados!")
        st.rerun()

    except Exception as e:
        st.error(f"Error crítico: {e}")

# --- 5. DISPLAY ---
if 'results' in st.session_state:
    df = pd.DataFrame(st.session_state.results)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏅 Ranking por Pedidos")
        # Sort by Pedidos descending
        st.table(df.sort_values("Pedidos", ascending=False)[["Surtidor", "Pedidos", "Piezas"]])
    
    with col2:
        st.subheader("⚠️ Historial de Ausencias")
        # Only show IDs with at least 1 absence
        st.table(df[df["Ausencias"] > 0][["Surtidor", "Ausencias", "Fechas"]])

    # CSV Download
    st.download_button("📥 Descargar Reporte CSV", df.to_csv(index=False), f"Reporte_{sel_month}.csv")
