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

    /* Backgrounds and removing the white top bar */
    .stApp { 
        background-color: #17202A; 
    }
    
    header {
        background-color: rgba(0,0,0,0) !important;
    }

    [data-testid="stHeader"] {
        background-color: #17202A !important;
    }
    
    /* SIDEBAR COMPACTO */
    [data-testid="stSidebar"] { 
        background-color: #111821 !important; 
        min-width: 350px !important; 
    }
    
    /* Table Styling */
    table { color: #FFFFFF !important; width: 100%; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; }

    /* Hide unnecessary UI elements */
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"] > span {
        display: none !important;
    }
    
    /* Spacing */
    [data-testid="stVerticalBlock"] > div { gap: 0.1rem !important; }
    
    /* Projection Boxes */
    .summary-box { 
        background-color: #212F3C; 
        padding: 12px; 
        border-radius: 8px; 
        margin-top: 5px; 
        border-left: 5px solid #C0392B; 
    }
    .summary-row { 
        display: flex; 
        justify-content: space-between; 
        border-bottom: 1px solid #2C3E50; 
        padding: 4px 0; 
        font-size: 0.9rem !important; 
    }
    .turn-pill { 
        background: #C0392B; 
        color: #FFFFFF !important; 
        padding: 2px 10px; 
        border-radius: 12px; 
        margin: 3px; 
        display: inline-block; 
        font-size: 0.85rem; 
        font-weight: bold; 
    }
    
    /* Buttons */
    div.stButton > button { 
        background-color: #C0392B !important; 
        color: #FFFFFF !important; 
        border: none;
        padding: 10px;
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
        with c1: st.markdown(f"**{sid}**")
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
    h_in = st.text_area("1. Histórico Acumulado (Mes)", height=150, placeholder="Pega aquí los datos históricos...")
with c2:
    t_in = st.text_area("2. Datos en Vivo (Hoy)", height=150, placeholder="Pega aquí los datos del día...")

if st.button("📊 ACTUALIZAR DASHBOARD"):
    pat = r"(\d+)\s+([A-Za-z0-9\s\.\-_]+?)\s+([\d\.]+)(?:\s+([\d\.]+))?"
    names_map, h_data, h_items = {}, {}, {}
    
    def clean_num(val):
        if not val: return 0
        return int(float(val.replace(',', '')))

    if h_in.strip():
        for sid_raw, name, count, items in re.findall(pat, h_in):
            sid = int(sid_raw)
            h_data[sid] = h_data.get(sid, 0) + clean_num(count)
            h_items[sid] = h_items.get(sid, 0) + clean_num(items)
            names_map[sid] = name.strip()

    t_data, t_items = {}, {}
    if t_in.strip():
        for sid_raw, name, count, items in re.findall(pat, t_in):
            sid = int(sid_raw)
            t_data[sid] = clean_num(count)
            t_items[sid] = clean_num(items)
            if sid not in names_map: names_map[sid] = name.strip()

    combined, current_scores = [], {}
    for sid in ALL_IDS:
        tot_p = h_data.get(sid, 0) + t_data.get(sid, 0)
        tot_i = h_items.get(sid, 0) + t_items.get(sid, 0)
        current_scores[sid] = tot_p
        if sid in active_ids or tot_p > 0:
            combined.append({
                "ID": sid, "Surtidor": names_map.get(sid, f"ID {sid}").upper(),
                "Pedidos": tot_p, "Piezas": tot_i
            })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = current_scores
    st.rerun()

# --- DISPLAY ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    
    # Tables and Charts
    col_left, col_right = st.columns([1.2, 0.8])

    with col_left:
        st.markdown("### 📈 Distribución de Carga")
        df['Label'] = "ID " + df['ID'].astype(str) + " - " + df['Surtidor']
        fig = px.pie(df, values='Pedidos', names='Label', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=13, textfont_color="white", marker=dict(line=dict(color='#17202A', width=2)))
        
        # INCREASED SIZE AND TRANSPARENCY
        fig.update_layout(
            height=750, 
            showlegend=False, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white"), 
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("### 🏆 Ranking")
        st.table(df[["Surtidor", "Pedidos", "Piezas"]])
        
        st.markdown("### ⚡ Eficiencia (8h)")
        df_eff = df.copy()
        df_eff['Ped/Hr'] = (df_eff['Pedidos'] / 8).round(1)
        df_eff['Pza/Hr'] = (df_eff['Piezas'] / 8).round(1)
        st.table(df_eff[['Surtidor', 'Ped/Hr', 'Pza/Hr']])

else:
    st.info("Ingresa los datos arriba para generar el análisis.")
