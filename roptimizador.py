import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# --- UI STYLE (EXACTLY AS YOU HAD IT) ---
st.set_page_config(page_title="Productividad Surtido", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
    <style>
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; }
    header, [data-testid="stHeader"] { background-color: #17202A !important; }
    [data-testid="stSidebar"] { background-color: #111821 !important; }
    .abs-container { background-color: #212F3C; padding: 20px; border-radius: 10px; border-left: 5px solid #C0392B; color: white; }
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .custom-table th { background-color: #2C3E50; border-bottom: 2px solid #C0392B; padding: 12px; text-align: left; color: white; }
    .custom-table td { border-bottom: 1px solid #34495E; padding: 10px; color: white; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    .date-tooltip { cursor: help; border-bottom: 2px dotted #E74C3C; color: #E74C3C; font-weight: bold; }
    div[data-testid="stNumberInput"] { width: 100px !important; }
    div[data-testid="stTextInput"] { width: 150px !important; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'abs_list' not in st.session_state: st.session_state.abs_list = []
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR (EXACTLY AS YOU HAD IT) ---
with st.sidebar:
    st.markdown("## ⚙️ Configuración")
    sidebar_limit = st.number_input("Mostrar hasta ID:", min_value=1, max_value=21, value=14)
    st.write("---")
    st.markdown("## ✅Asistencia/Comida🍱")
    if st.button("⌨️ MODO MANUAL" if not st.session_state.manual_mode else "🌐 MODO AUTO"):
        st.session_state.manual_mode = not st.session_state.manual_mode
        st.rerun()
    active_ids = []
    st.write("---")
    c1, c2, c3 = st.columns([2, 1, 1])
    c1.markdown("**ID**")
    c2.markdown("**On**")
    c3.markdown("🍴")
    for sid in ALL_IDS:
        if sid <= sidebar_limit:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1: st.markdown(f"**Surtidor {sid}**")
            with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
            with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
            if on and not meal: active_ids.append(sid)
    st.write("---")
    btn_label = "👁️ OCULTAR TURNOS" if st.session_state.show_turns else "🚀 GENERAR TURNOS"
    if st.button(btn_label):
        st.session_state.show_turns = not st.session_state.show_turns
        st.rerun()

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    abs_data = []
    
    # Generic cleaner for Productivity Grid
    def clean_val(v):
        try:
            val_str = str(v).strip().replace(',', '').replace('.', '')
            return int(float(val_str)) if val_str not in ["", "-", "nan"] else 0
        except: return 0

    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
        rows, cols = df_raw.shape

        # 1. Main Grid Logic (Productivity)
        for r in range(rows):
            for c in range(cols):
                cell_val = str(df_raw.iloc[r, c]).strip()
                if cell_val.isdigit():
                    sid = int(cell_val)
                    if sid in ALL_IDS:
                        p_val = clean_val(df_raw.iloc[r, c + 2]) if c+2 < cols else 0
                        i_val = clean_val(df_raw.iloc[r, c + 3]) if c+3 < cols else 0
                        data_p[sid] = data_p.get(sid, 0) + p_val
                        data_i[sid] = data_i.get(sid, 0) + i_val
        
        # 2. Ausencias Feature (Table J2:L23)
        # J=Index 9, K=Index 10, L=Index 11
        for r in range(2, 23): # Skip header rows
            if r < rows:
                # Get raw values
                id_val = str(df_raw.iloc[r, 9]).strip() # Col J
                count_val = str(df_raw.iloc[r, 10]).strip() # Col K
                dates_val = str(df_raw.iloc[r, 11]).strip() # Col L

                # Convert Count properly (ignore decimals, don't multiply by 100)
                try:
                    actual_count = int(float(count_val)) if count_val not in ["nan", ""] else 0
                except: actual_count = 0

                # Use the ID directly from Col J
                try:
                    sid_int = int(float(id_val))
                except: sid_int = 0
                
                if sid_int > 0:
                    date_list = [d.strip() for d in dates_val.split(',')] if dates_val != "nan" else []
                    abs_data.append({
                        "Surtidor": f"Surtidor {sid_int}", 
                        "ID": sid_int, 
                        "Count": actual_count, 
                        "Dates": date_list
                    })
                            
    except Exception as e:
        st.error(f"Error: {e}")

    ranking_list = [{"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)} for s in range(1, sidebar_limit + 1)]
    st.session_state.final_ranking = sorted(ranking_list, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {s: data_p.get(s, 0) for s in ALL_IDS}
    st.session_state.abs_list = abs_data
    st.rerun()

# --- VISUALS ---
if st.session_state.final_ranking:
    full_df = pd.DataFrame(st.session_state.final_ranking)
    df_active = full_df[full_df['Pedidos'] > 0].copy()
    
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        fig = px.pie(df_active, values='Pedidos', names='Surtidor', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_layout(height=350, showlegend=False, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    with col_table:
        st.markdown("### 🏅 Ranking")
        st.table(df_active[["Surtidor", "Pedidos", "Piezas"]])

    # --- AUSENCIAS SECTION ---
    st.write("---")
    st.markdown("### ⚠️ AUSENCIAS")
    filter_input = st.text_input("Filtro (ID o 'T' para ausentes):", key="abs_filter").strip().upper()
    
    filtered_abs = []
    total_abs_count = 0
    for item in st.session_state.abs_list:
        show = (filter_input == "T" and item['Count'] > 0) or (filter_input == "") or (filter_input.isdigit() and int(filter_input) == item['ID'])
        if show:
            filtered_abs.append(item)
            total_abs_count += item['Count']

    rows_html = ""
    for item in filtered_abs:
        dates_str = " | ".join(item['Dates']) if item['Dates'] else "Sin fechas"
        rows_html += f"<tr><td>{item['Surtidor']}</td><td><span class='date-tooltip' title='{dates_str}'>{item['Count']} días</span></td></tr>"

    table_content = f"""<div class="abs-container"><h4 style="margin:0 0 10px 0;">Inasistencias en vista: {total_abs_count}</h4><table class="custom-table"><thead><tr><th>Surtidor</th><th>Ausencias (Hover para fechas)</th></tr></thead><tbody>{rows_html if rows_html else "<tr><td colspan='2'>No hay coincidencias</td></tr>"}</tbody></table></div>"""
    st.markdown(table_content, unsafe_allow_html=True)
