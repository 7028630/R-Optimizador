import streamlit as st
import re
import pandas as pd

# --- 1. THE MASTER KEY ---
# Open one of your daily links. Look at the URL. 
# Whatever number follows 'gid=' is what you put here.
# Usually, the first tab is 0, but since you have multiple, it might be different.
DAILY_TAB_GID = "0" 

MONTH_GIDS = {
    "ABRIL 2026": "2083245391",
}
BASE_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid="

# --- 2. THE "I CAN ACTUALLY SEE IT" STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #17202A; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }
    
    /* THE BUTTON: Absolute Contrast (Red with Black Text) */
    div.stButton > button { 
        background-color: #FF0000 !important; 
        color: #000000 !important; 
        font-weight: 900 !important;
        border: 4px solid #FFFFFF !important;
        height: 4em !important;
        font-size: 1.2rem !important;
    }
    
    /* Table Fix */
    .stTable, .stDataFrame { background-color: #1C2833 !important; border: 1px solid #34495E; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    sel_month = st.selectbox("Mes Actual:", list(MONTH_GIDS.keys()))
    limit = st.number_input("IDs (1-14 o 1-21):", 1, 21, 14)
    MASTER_URL = f"{BASE_URL}{MONTH_GIDS[sel_month]}"

# --- 4. THE BRAIN (WITH DEBUGGING) ---
st.title(f"🚀 Panel: {sel_month}")

if st.button("ACTUALIZAR DATOS DE LA LISTA"):
    try:
        master_df = pd.read_csv(MASTER_URL)
        
        totals_p = {i: 0 for i in range(1, limit + 1)}
        totals_i = {i: 0 for i in range(1, limit + 1)}
        abs_dates = {i: [] for i in range(1, limit + 1)}

        status = st.empty()
        debug_area = st.expander("🛠 Ver lo que Python está leyendo (Debug)")

        for index, row in master_df.iterrows():
            fecha = str(row.iloc[0])
            url_raw = str(row.iloc[1])
            
            if "/edit" in url_raw:
                csv_url = url_raw.split('/edit')[0] + f"/export?format=csv&gid={DAILY_TAB_GID}"
                
                try:
                    # header=None helps us see exactly which column is which
                    day_df = pd.read_csv(csv_url)
                    
                    # DEBUG: Let's see the first row of the first link to verify columns
                    if index == 0:
                        debug_area.write("Columnas detectadas en el primer link:")
                        debug_area.dataframe(day_df.head(3))

                    for sid in range(1, limit + 1):
                        # Use Index 1 for Column B (ID)
                        # Use Index 3 for Column D (Pedidos)
                        # Use Index 4 for Column E (Piezas)
                        match = day_df[day_df.iloc[:, 1].astype(str).str.strip() == str(sid)]
                        
                        if not match.empty:
                            p_raw = str(match.iloc[0, 3]).replace('.', '').replace(',', '')
                            i_raw = str(match.iloc[0, 4]).replace('.', '').replace(',', '')
                            
                            p_val = int(float(p_raw)) if p_raw.replace('nan','0').replace('.','').isdigit() else 0
                            i_val = int(float(i_raw)) if i_raw.replace('nan','0').replace('.','').isdigit() else 0
                            
                            totals_p[sid] += p_val
                            totals_i[sid] += i_val
                            if p_val == 0:
                                abs_dates[sid].append(fecha)
                except Exception as e:
                    debug_area.error(f"Error en link {fecha}: {e}")
                    continue
            
            status.text(f"Calculando... {fecha}")

        st.session_state.results = [
            {"Surtidor": f"Surtidor {s}", "Pedidos": totals_p[s], "Piezas": totals_i[s], 
             "Ausencias": len(abs_dates[s]), "Fechas": ", ".join(abs_dates[s])}
            for s in range(1, limit + 1)
        ]
        status.success("¡Listo!")
        st.rerun()

    except Exception as e:
        st.error(f"Error en la lista maestra: {e}")

# --- 5. THE RESULTS ---
if 'results' in st.session_state:
    df = pd.DataFrame(st.session_state.results)
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏅 Ranking")
        st.table(df.sort_values("Pedidos", ascending=False)[["Surtidor", "Pedidos", "Piezas"]])
    
    with c2:
        st.subheader("⚠️ Ausencias")
        st.table(df[df["Ausencias"] > 0][["Surtidor", "Ausencias", "Fechas"]])
