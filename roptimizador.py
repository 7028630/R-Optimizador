import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) # Expanded to cover all possible IDs in your list
KNOWN_FIXES = {
    6: "LIDERES DE OPERACIONES",
    7: "C. GARCIA",
    12: "R. GONZALEZ",
    13: "J. PEREZ",
    14: "J. SILVA",
    18: "LIDERES DE OPERACIONES"
}

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; }
    header, [data-testid="stHeader"] { background-color: #17202A !important; }
    [data-testid="stSidebar"] { background-color: #111821 !important; min-width: 320px !important; }
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; text-align: left; padding: 8px; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; padding: 8px; }
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"] > span { display: none !important; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; }
    .turn-pill { background: #C0392B; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}

# --- SIDEBAR: DISPONIBILIDAD ---
with st.sidebar:
    st.markdown("## ⚙️ Disponibilidad")
    if st.button("🗑️ REINICIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    active_ids = []
    st.write("---")
    for sid in ALL_IDS:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.markdown(f"**ID {sid}**")
        with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with col3: meal = st.toggle("🍴", key=f"m_{sid}", label_visibility="collapsed")
        if on and not meal: active_ids.append(sid)

# --- MAIN CONTENT ---
st.title("🏆 Dashboard de Productividad")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Histórico Acumulado", height=150, placeholder="Pega el historial aquí...")
with c2:
    t_in = st.text_area("2. Live Data (Hoy)", height=150, placeholder="Pega los datos de hoy aquí...")

if st.button("📊 PROCESAR Y ACTUALIZAR"):
    # Improved Regex: Handles IDs, Names (or lack thereof), and Numbers with decimals/commas
    # Group 1: ID, Group 2: Name (optional), Group 3: Pedidos, Group 4: Piezas
    pat = r"(\d+)\s+([A-Za-z\s\.\-_]+|[0\s\-]+)?\s*([\d\.,]+)\s+([\d\.,\-]+)"
    
    data_p, data_i, names_map = {}, {}, {}

    def clean_val(v):
        if not v or '-' in str(v): return 0
        return int(float(str(v).replace(',', '')))

    # Process History and Today
    for raw_text in [h_in, t_in]:
        if raw_text.strip():
            matches = re.findall(pat, raw_text)
            for sid_raw, name_raw, ped, pza in matches:
                sid = int(sid_raw)
                data_p[sid] = data_p.get(sid, 0) + clean_val(ped)
                data_i[sid] = data_i.get(sid, 0) + clean_val(pza)
                
                # Logic to determine the name
                raw_n = str(name_raw).strip().upper() if name_raw else ""
                if sid in KNOWN_FIXES and (not raw_n or "0" in raw_n or "-" in raw_n):
                    names_map[sid] = KNOWN_FIXES[sid]
                elif raw_n and not raw_n.isdigit():
                    names_map[sid] = raw_n
                elif sid not in names_map:
                    names_map[sid] = KNOWN_FIXES.get(sid, f"ID {sid}")

    combined = []
    for sid, peds in data_p.items():
        if peds > 0 or data_i.get(sid, 0) > 0:
            combined.append({
                "ID": sid,
                "Surtidor": names_map.get(sid, f"ID {sid}"),
                "Pedidos": peds,
                "Piezas": data_i.get(sid, 0)
            })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {sid: data_p.get(sid, 0) for sid in ALL_IDS}
    st.rerun()

# --- VISUALIZATION ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1) # Start Rank at 1

    col_chart, col_table = st.columns([1.3, 0.7])

    with col_chart:
        df['Label'] = "ID " + df['ID'].astype(str) + " - " + df['Surtidor']
        fig = px.pie(df, values='Pedidos', names='Label', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#17202A', width=2)))
        fig.update_layout(
            height=850, # EXTRA LARGE PIE CHART
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("### 🏅 Ranking de Surtido")
        st.table(df[["Surtidor", "Pedidos", "Piezas"]])
        
        st.markdown("### ⚡ Rendimiento Promedio")
        df_eff = df.copy()
        df_eff['P/Hr'] = (df_eff['Pedidos'] / 8).round(1)
        st.table(df_eff[['Surtidor', 'P/Hr']])
else:
    st.info("💡 Pega los datos arriba y presiona el botón para visualizar el ranking.")
