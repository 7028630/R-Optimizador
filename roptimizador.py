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
    /* Global Font Arial */
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3 {
        font-family: Arial, Helvetica, sans-serif !important;
    }

    /* Hide the 'keyboard_double_arrow' ghost text and extra sidebar icons */
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"] > span {
        display: none !important;
    }
    
    .stApp { background-color: #EAECEE; color: #1C2833; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #17202A !important; min-width: 420px !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { 
        color: #FFFFFF !important; 
    }
    
    /* Spacing for Availability Toggles */
    .stCheckbox, .stToggleButton {
        margin-bottom: 15px !important;
    }
    
    .summary-box { background-color: #212F3C; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #34495E; color: #FFFFFF !important; }
    .summary-row { display: flex; justify-content: space-between; border-bottom: 1px solid #2C3E50; padding: 5px 0; font-size: 0.95rem !important; }
    .turn-pill { background: #E74C3C; color: white; padding: 4px 10px; border-radius: 8px; margin: 3px; display: inline-block; font-size: 0.85rem; border: 1px solid #566573; font-weight: bold; }
    
    div.stButton > button { 
        background-color: #C0392B !important; 
        color: white !important; 
        border-radius: 8px !important; 
        font-weight: 900 !important; 
        width: 100% !important; 
    }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}

# --- SIDEBAR: DISPONIBILIDAD & PRÓXIMOS 20 ---
with st.sidebar:
    st.markdown("## ⚙️ Disponibilidad")
    if st.button("🗑️ REINICIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    st.write("---")
    active_ids = []
    # Encabezados con más espacio
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
        if on and not meal: active_ids.append(sid)

    if st.session_state.scores and active_ids:
        st.write("---")
        st.markdown("### 🔄 Proyección: Siguientes 20")
        ts = st.session_state.scores.copy()
        turns, counts = [], {}
        for _ in range(20):
            valid_scores = {k: v for k, v in ts.items() if k in active_ids}
            if not valid_scores: break
            next_id = min(valid_scores, key=valid_scores.get)
            turns.append(next_id); counts[next_id] = counts.get(next_id, 0) + 1; ts[next_id] += 1
        
        st.markdown("".join([f'<span class="turn-pill">{t}</span>' for t in turns]), unsafe_allow_html=True)
        
        summary_html = '<div class="summary-box"><b>Turnos a asignar:</b>'
        for sid, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            summary_html += f'<div class="summary-row"><span>ID {sid}</span> <span>{count} pedidos</span></div>'
        st.markdown(summary_html + '</div>', unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("🏆 Dashboard de Productividad")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Pega aquí el cuadro de productividad de cada día del mes hasta ahora", height=150)
with c2:
    t_in = st.text_area("2. Totales del día actual", height=150)

if st.button("📊 ACTUALIZAR DASHBOARD"):
    # REVISIÓN DE REGEX: Permite números, espacios, puntos y letras (Ej: "4 O. DAVILA 136")
    # Captura: (ID) (Nombre con puntos/espacios) (Pedidos) (Piezas opcional)
    pat = r"(\d+)\s+([A-Za-z\s\.\-_]+?)\s+(\d+)(?:\s+(\d+))?"
    
    names_map, historical_data, historical_items = {}, {}, {}
    
    # Procesar Mes
    if h_in.strip():
        for sid_raw, name, count, items in re.findall(pat, h_in):
            sid = int(sid_raw)
            historical_data[sid] = historical_data.get(sid, 0) + int(count)
            historical_items[sid] = historical_items.get(sid, 0) + (int(items) if items and items.isdigit() else 0)
            names_map[sid] = name.strip()

    # Procesar Hoy
    today_data, today_items = {}, {}
    if t_in.strip():
        for sid_raw, name, count, items in re.findall(pat, t_in):
            sid = int(sid_raw)
            today_data[sid] = int(count)
            today_items[sid] = (int(items) if items and items.isdigit() else 0)
            if sid not in names_map: names_map[sid] = name.strip()

    combined, current_scores = [], {}
    for sid in ALL_IDS:
        h_val, t_val = historical_data.get(sid, 0), today_data.get(sid, 0)
        h_itm, t_itm = historical_items.get(sid, 0), today_items.get(sid, 0)
        total_p, total_i = h_val + t_val, h_itm + t_itm
        current_scores[sid] = total_p
        
        if sid in active_ids or total_p > 0:
            combined.append({
                "ID": sid, 
                "Surtidor": names_map.get(sid, f"Surtidor {sid}").upper(),
                "Histórico": h_val, 
                "Hoy": t_val, 
                "Total Pedidos": total_p, 
                "Total Piezas": total_i
            })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Total Pedidos'], reverse=True)
    st.session_state.scores = current_scores
    st.rerun()

# --- DISPLAY ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1)
    df.index.name = "Puesto"

    st.subheader("📋 Tabla de Posiciones (Ordenada por Total)")
    st.dataframe(df.style.format({
        "Histórico": "{:,.0f}", "Hoy": "{:,.0f}", 
        "Total Pedidos": "{:,.0f}", "Total Piezas": "{:,.0f}"
    }), use_container_width=True)

    col_chart, col_efficiency = st.columns([1.3, 0.7])

    with col_chart:
        st.subheader("📈 Participación en Volumen")
        df['Label'] = "ID " + df['ID'].astype(str) + " - " + df['Surtidor']
        fig = px.pie(df, values='Total Pedidos', names='Label', hole=.3,
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        
        fig.update_traces(textinfo='percent+label', textfont_size=13)
        fig.update_layout(height=650, font_family="Arial", showlegend=True,
                          margin=dict(t=20, b=20, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

    with col_efficiency:
        st.subheader("⚡ Eficiencia (Promedio 8h)")
        df_eff = df.copy()
        df_eff['Ped/Hr'] = (df_eff['Total Pedidos'] / 8).round(2)
        df_eff['Pza/Hr'] = (df_eff['Total Piezas'] / 8).round(2)
        st.table(df_eff[['Surtidor', 'Ped/Hr', 'Pza/Hr']])
        st.caption("Basado en jornada diaria de 8 horas.")

else:
    st.info("Configura la disponibilidad y pega los datos para generar el dashboard.")
