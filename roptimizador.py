import streamlit as st
import re
from datetime import datetime

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
    
    /* TABLE STYLING */
    .rank-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .rank-table th { background-color: #C0392B; color: white; padding: 12px; text-align: left; }
    .rank-table td { padding: 10px; border-bottom: 1px solid #D5DBDB; color: #1C2833; }
    .rank-table tr:nth-child(even) { background-color: #F4F6F7; }
    
    .leader-row { background-color: #FDEDEC !important; font-weight: bold; border-left: 5px solid #C0392B; }
    .id-pill { background: #17202A; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
    
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
        
        # Solo se consideran para el ranking si están On y no están comiendo
        if on and not meal:
            active_ids.append(sid)

# --- MAIN CONTENT ---
st.title("🏆 Ranking Mensual Consolidado")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Productividad del mes hasta ahora", height=150, 
                        placeholder="Pega aquí el cuadro de productividad de cada día del mes...")
with c2:
    t_in = st.text_area("2. Totales del día actual", height=150, 
                        placeholder="Pega aquí los totales que van hoy...")

if st.button("📊 ACTUALIZAR RANKING"):
    pat = r"(\d+)\s+([A-Z\s\.\-_]+?)\s+(\d+)"
    names_map = {}
    historical_data = {}
    
    # Procesar histórico
    if h_in.strip():
        matches = re.findall(pat, h_in)
        for sid_raw, name, count in matches:
            sid = int(sid_raw)
            historical_data[sid] = historical_data.get(sid, 0) + int(count)
            names_map[sid] = name.strip()

    # Procesar hoy
    today_data = {}
    if t_in.strip():
        matches_today = re.findall(pat, t_in)
        for sid_raw, name, count in matches_today:
            sid = int(sid_raw)
            today_data[sid] = int(count)
            if sid not in names_map: names_map[sid] = name.strip()

    # Consolidar solo para los IDs activos seleccionados en la barra lateral
    combined = []
    for sid in active_ids:
        h_val = historical_data.get(sid, 0)
        t_val = today_data.get(sid, 0)
        combined.append({
            "ID": sid,
            "Nombre": names_map.get(sid, f"ID {sid}"),
            "Historico": h_val,
            "Hoy": t_val,
            "Total": h_val + t_val
        })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Total'], reverse=True)
    st.rerun()

# --- DISPLAY ---
if st.session_state.final_ranking:
    st.write("---")
    table_html = """
    <table class="rank-table">
        <thead>
            <tr>
                <th>Puesto</th>
                <th>ID</th>
                <th>Surtidor</th>
                <th>Histórico</th>
                <th>Hoy</th>
                <th>Total Acumulado</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for i, row in enumerate(st.session_state.final_ranking):
        rank_class = "leader-row" if i == 0 else ""
        table_html += f"""
            <tr class="{rank_class}">
                <td>#{i+1}</td>
                <td><span class="id-pill">{row['ID']}</span></td>
                <td>{row['Nombre']}</td>
                <td>{row['Historico']}</td>
                <td>{row['Hoy']}</td>
                <td>{row['Total']}</td>
            </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("Configura la disponibilidad y pega los datos para ver el ranking de los surtidores activos.")
