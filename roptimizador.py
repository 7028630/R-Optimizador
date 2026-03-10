import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")

st.markdown("""
    <style>
    /* Global Font Arial & Force White Text */
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }

    /* Background Principal */
    .stApp { background-color: #17202A; } 

    /* CAMUFLAJE DE LA BARRA SUPERIOR (TOOLBAR) */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    [data-testid="stAppToolbar"] {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    
    /* SIDEBAR COMPACTO */
    [data-testid="stSidebar"] { 
        background-color: #111821 !important; 
        min-width: 350px !important; 
    }
    
    /* Force Table Text to White & Arial */
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; font-family: Arial !important; text-align: left; padding: 10px; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50; padding: 8px; font-family: Arial !important; }

    /* Hide Ghost Icons & Extra padding */
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"] > span { display: none !important; }
    [data-testid="stVerticalBlock"] > div { gap: 0.02rem !important; }
    .stCheckbox, .stToggleButton, .stMarkdown p { margin-bottom: 0px !important; padding-bottom: 0px !important; }

    /* Projection Boxes */
    .summary-box { 
        background-color: #212F3C; 
        padding: 8px; 
        border-radius: 8px; 
        margin-top: 5px; 
        border: 1px solid #C0392B; 
    }
    .summary-row { 
        display: flex; 
        justify-content: space-between; 
        border-bottom: 1px solid #2C3E50; 
        padding: 2px 0; 
        font-size: 0.85rem !important; 
        color: #FFFFFF !important;
    }
    .turn-pill { 
        background: #C0392B; 
        color: #FFFFFF !important; 
        padding: 2px 8px; 
        border-radius: 6px; 
        margin: 2px; 
        display: inline-block; 
        font-size: 0.8rem; 
        font-weight: bold; 
    }
    
    /* Red Buttons */
    div.stButton > button { 
        background-color: #C0392B !important; 
        color: #FFFFFF !important; 
        border-radius: 8px !important; 
        font-weight: bold !important; 
        width: 100% !important; 
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
    
    st.write("---")
    active_ids = []
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 1, 1, 1])
    with h_col1: st.markdown("**ID**")
    with h_col2: st.markdown("**On**")
    with h_col3: st.markdown("**🍴**")
    with h_col4: st.markdown("**Exc.**")
    
    for sid in ALL_IDS:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1: st.markdown(f"**ID {sid}**")
        with c2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with c3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        with c4: pdr = st.checkbox("", key=f"p_{sid}", label_visibility="collapsed")
        if on and not meal: active_ids.append(sid)

    if st.session_state.scores and active_ids:
        st.write("---")
        st.markdown("### 🔄 Siguientes 20")
        ts = st.session_state.scores.copy()
        turns, counts = [], {}
        for _ in range(20):
            valid_scores = {k: v for k, v in ts.items() if k in active_ids}
            if not valid_scores: break
            next_id = min(valid_scores, key=valid_scores.get)
            turns.append(next_id); counts[next_id] = counts.get(next_id, 0) + 1; ts[next_id] += 1
        
        st.markdown("".join([f'<span class="turn-pill">{t}</span>' for t in turns]), unsafe_allow_html=True)
        summary_html = '<div class="summary-box">'
        for sid, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            summary_html += f'<div class="summary-row"><span>ID {sid}</span> <span>{count} pzs</span></div>'
        st.markdown(summary_html + '</div>', unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("🏆 Dashboard de Productividad")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Productividad Acumulada del Mes", height=100)
with c2:
    t_in = st.text_area("2. Productividad del Día", height=100)

if st.button("📊 ACTUALIZAR DASHBOARD"):
    pat = r"(\d+)\s+([A-Za-z0-9\s\.\-_]+?)\s+(\d+)(?:\s+(\d+))?"
    names_map, h_data, h_items = {}, {}, {}
    
    if h_in.strip():
        for sid_raw, name, count, items in re.findall(pat, h_in):
            sid = int(sid_raw)
            h_data[sid] = h_data.get(sid, 0) + int(count)
            h_items[sid] = h_items.get(sid, 0) + (int(items) if items and items.isdigit() else 0)
            names_map[sid] = name.strip()

    t_data, t_items = {}, {}
    if t_in.strip():
        for sid_raw, name, count, items in re.findall(pat, t_in):
            sid = int(sid_raw)
            t_data[sid] = int(count)
            t_items[sid] = (int(items) if items and items.isdigit() else 0)
            if sid not in names_map: names_map[sid] = name.strip()

    combined, current_scores = [], {}
    for sid in ALL_IDS:
        tot_p = h_data.get(sid, 0) + t_data.get(sid, 0)
        tot_i = h_items.get(sid, 0) + t_items.get(sid, 0)
        current_scores[sid] = tot_p
        if sid in active_ids or tot_p > 0:
            combined.append({
                "ID": sid, "Surtidor": names_map.get(sid, f"ID {sid}").upper(),
                "Histórico": h_data.get(sid, 0), "Hoy": t_data.get(sid, 0), 
                "Total Pedidos": tot_p, "Total Piezas": tot_i
            })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Total Pedidos'], reverse=True)
    st.session_state.scores = current_scores
    st.rerun()

# --- DISPLAY ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1)
    df.index.name = "Rank"

    # Ranking Table
    st.markdown("### 📋 Tabla de Posiciones")
    st.table(df[["Surtidor", "Total Pedidos", "Total Piezas"]])

    col_chart, col_efficiency = st.columns([1.1, 0.9])

    with col_chart:
        df['Label'] = "ID " + df['ID'].astype(str) + " - " + df['Surtidor']
        fig = px.pie(df, values='Total Pedidos', names='Label', hole=.3,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=12, textfont_color="white")
        fig.update_layout(height=450, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', 
                          font=dict(color="white"), margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_efficiency:
        st.markdown("### ⚡ Eficiencia (8h)")
        df_eff = df.copy()
        df_eff['Ped/Hr'] = (df_eff['Total Pedidos'] / 8).round(2)
        df_eff['Pza/Hr'] = (df_eff['Total Piezas'] / 8).round(2)
        st.table(df_eff[['Surtidor', 'Ped/Hr', 'Pza/Hr']])

else:
    st.info("Pega los datos para activar el dashboard.")
