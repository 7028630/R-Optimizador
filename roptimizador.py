import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
# Manual mapping for IDs that often appear broken in raw data
KNOWN_FIXES = {
    6: "LIDERES DE OPERACIONES",
    12: "J. SILVA"
}

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")

st.markdown("""
    <style>
    /* Global Font Arial & Force White Text */
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }

    /* Backgrounds & Removing the top white bar */
    .stApp { background-color: #17202A; }
    header, [data-testid="stHeader"] { background-color: #17202A !important; }
    
    /* SIDEBAR COMPACTO */
    [data-testid="stSidebar"] { 
        background-color: #111821 !important; 
        min-width: 320px !important; 
    }
    
    /* Table Styling */
    table { color: #FFFFFF !important; width: 100%; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; }

    /* Hide unnecessary UI elements */
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"] > span {
        display: none !important;
    }
    
    /* Projection Boxes */
    .summary-box { 
        background-color: #212F3C; 
        padding: 10px; 
        border-radius: 8px; 
        border-left: 5px solid #C0392B; 
    }
    .turn-pill { 
        background: #C0392B; 
        padding: 2px 8px; 
        border-radius: 10px; 
        margin: 2px; 
        display: inline-block; 
        font-size: 0.8rem; 
        font-weight: bold; 
    }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #C0392B !important; 
        color: #FFFFFF !important; 
        border-radius: 5px !important;
        font-weight: bold !important; 
    }
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

    if st.session_state.scores and active_ids:
        st.write("---")
        st.markdown("### 🔄 Siguientes 20")
        ts = st.session_state.scores.copy()
        turns = []
        for _ in range(20):
            valid_scores = {k: v for k, v in ts.items() if k in active_ids}
            if not valid_scores: break
            next_id = min(valid_scores, key=valid_scores.get)
            turns.append(next_id); ts[next_id] += 1
        st.markdown("".join([f'<span class="turn-pill">{t}</span>' for t in turns]), unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("🏆 Dashboard de Productividad")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Datos Históricos", height=150, placeholder="Pega el historial aquí...")
with c2:
    t_in = st.text_area("2. Datos en Vivo (Hoy)", height=150, placeholder="Pega los datos de hoy aquí...")

if st.button("📊 GENERAR DASHBOARD"):
    # Pattern designed to handle names, ID numbers, and piece counts
    pat = r"(\d+)\s+([A-Za-z0-9\s\.\-_]+?)\s+([\d\.]+)\s+([\d\.\-]+)"
    names_map, data_p, data_i = {}, {}, {}

    def clean(v): return int(float(str(v).replace(',', '').replace('-', '0')))

    # Process both inputs
    for raw_text in [h_in, t_in]:
        if raw_text.strip():
            matches = re.findall(pat, raw_text)
            for sid_raw, name_raw, ped, pza in matches:
                sid = int(sid_raw)
                data_p[sid] = data_p.get(sid, 0) + clean(ped)
                data_i[sid] = data_i.get(sid, 0) + clean(pza)
                
                # Cleanup names and apply hardcoded fixes for 6 and 12
                clean_name = name_raw.strip().upper()
                if sid in KNOWN_FIXES and ("-" in clean_name or clean_name == "0"):
                    names_map[sid] = KNOWN_FIXES[sid]
                else:
                    names_map[sid] = clean_name

    combined = []
    for sid in set(list(data_p.keys()) + list(names_map.keys())):
        combined.append({
            "ID": sid,
            "Surtidor": names_map.get(sid, f"ID {sid}"),
            "Pedidos": data_p.get(sid, 0),
            "Piezas": data_i.get(sid, 0)
        })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {sid: data_p.get(sid, 0) for sid in ALL_IDS}
    st.rerun()

# --- VISUALIZATION ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1) # Start rank at 1

    col_chart, col_table = st.columns([1.3, 0.7])

    with col_chart:
        df['Label'] = "ID " + df['ID'].astype(str) + " - " + df['Surtidor']
        fig = px.pie(df, values='Pedidos', names='Label', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#17202A', width=2)))
        fig.update_layout(
            height=800, # BIGGER PIE CHART
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("### 🏅 Ranking General")
        st.table(df[["Surtidor", "Pedidos", "Piezas"]])
        
        st.markdown("### ⚡ Metas (8h)")
        df_eff = df.copy()
        df_eff['P/Hr'] = (df_eff['Pedidos'] / 8).round(1)
        st.table(df_eff[['Surtidor', 'P/Hr']])
else:
    st.info("Pega los datos arriba para actualizar los resultados.")
