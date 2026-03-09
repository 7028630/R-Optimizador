import streamlit as st
import re
import pandas as pd

# --- CONFIGURATION ---
ALL_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #EAECEE; color: #1C2833; }
    [data-testid="stSidebar"] { background-color: #17202A !important; min-width: 420px !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: #FFFFFF !important; }
    div.stButton > button { background-color: #C0392B !important; color: white !important; border-radius: 8px !important; font-weight: 900 !important; width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []

# --- SIDEBAR: DISPONIBILIDAD ---
with st.sidebar:
    st.markdown("### ⚙️ Disponibilidad")
    if st.button("🗑️ REINICIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    st.write("---")
    active_ids = []
    h_col1, h_col2, h_col3, h_col4 = st.columns([1.5, 1.2, 1, 1])
    with h_col1: st.write("**ID**")
    with h_col2: st.write("**On**")
    with h_col3: st.write("**🍴**")
    with h_col4: st.write("**Exc.**")
    
    for sid in ALL_IDS:
        c1, c2, c3, c4 = st.columns([1.5, 1.2, 1, 1])
        with c1: st.write(f"ID {sid}")
        with c2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with c3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        with c4: pdr = st.checkbox("", key=f"p_{sid}", label_visibility="collapsed")
        
        if on and not meal:
            active_ids.append(sid)

# --- MAIN CONTENT ---
st.title("🏆 Ranking Mensual Consolidado")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Cuadro de productividad de cada día del mes", height=150, 
                        placeholder="Pega aquí los datos acumulados del mes...")
with c2:
    t_in = st.text_area("2. Totales del día actual", height=150, 
                        placeholder="Pega aquí los totales de hoy...")

if st.button("📊 ACTUALIZAR RANKING"):
    # Updated regex to be more forgiving with names and spaces
    pat = r"(\d+)\s+([A-Z\s\.\-_]+?)\s+(\d+)"
    names_map = {}
    historical_data = {}
    
    if h_in.strip():
        matches = re.findall(pat, h_in)
        for sid_raw, name, count in matches:
            sid = int(sid_raw)
            historical_data[sid] = historical_data.get(sid, 0) + int(count)
            names_map[sid] = name.strip()

    today_data = {}
    if t_in.strip():
        matches_today = re.findall(pat, t_in)
        for sid_raw, name, count in matches_today:
            sid = int(sid_raw)
            today_data[sid] = int(count)
            if sid not in names_map: names_map[sid] = name.strip()

    combined = []
    for sid in active_ids:
        h_val = historical_data.get(sid, 0)
        t_val = today_data.get(sid, 0)
        combined.append({
            "ID": sid,
            "Surtidor": names_map.get(sid, f"ID {sid}"),
            "Histórico": h_val,
            "Hoy": t_val,
            "Total": h_val + t_val
        })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Total'], reverse=True)
    st.rerun()

# --- DISPLAY ---
if st.session_state.final_ranking:
    st.write("---")
    
    # Create a DataFrame for reliable display
    df = pd.DataFrame(st.session_state.final_ranking)
    
    # Add Rank column at the start
    df.index = range(1, len(df) + 1)
    df.index.name = "Puesto"
    
    # Format IDs to remove decimals if they appear
    df['ID'] = df['ID'].astype(str)

    # Use st.dataframe for an interactive, bug-free table
    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "Total": st.column_config.NumberColumn(format="%d 📦"),
            "Histórico": st.column_config.NumberColumn(format="%d"),
            "Hoy": st.column_config.NumberColumn(format="%d"),
        }
    )
    
    # Highlight the winner visually with a Big Number
    top_name = st.session_state.final_ranking[0]['Surtidor']
    top_score = st.session_state.final_ranking[0]['Total']
    st.success(f"🥇 **Líder Actual:** {top_name} con **{top_score}** pedidos acumulados.")

else:
    st.info("Configura la disponibilidad y pulsa el botón para generar el ranking.")
