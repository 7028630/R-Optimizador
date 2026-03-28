import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# --- UI STYLE ---
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
    
    /* Table Styling */
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

# Initialize Session States
if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'abs_list' not in st.session_state: st.session_state.abs_list = []
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR ---
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

    if st.session_state.show_turns and st.session_state.scores and active_ids:
        st.markdown("### ⏭️ Turnos")
        temp_scores = st.session_state.scores.copy()
        simulated_turns = []
        for _ in range(20):
            valid_cands = {k: v for k, v in temp_scores.items() if k in active_ids}
            if not valid_cands: break
            next_p = min(valid_cands, key=valid_cands.get)
            simulated_turns.append(next_p)
            temp_scores[next_p] += 1
        st.markdown("".join([f'<span class="turn-pill">S{t}</span>' for t in simulated_turns]), unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    abs_data = []
    
    def clean_val(v):
        try:
            val_str = str(v).strip().replace(',', '').replace('.', '')
            return int(float(val_str)) if val_str not in ["", "-", "nan"] else 0
        except: return 0

    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
        rows, cols = df_raw.shape

        # 1. Main Data Extraction (Productivity)
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
        
        # 2. Ausencias Feature (Feeding from J2:L23)
        # Skip 2 rows of headers (index 0 and 1)
        for r in range(2, 23):
            if r < rows:
                # Column J=9 (Dates), K=10 (Count), L=11 (ID Name)
                raw_dates = str(df_raw.iloc[r, 9]).strip() if cols > 9 else ""
                abs_count = clean_val(df_raw.iloc[r, 10]) if cols > 10 else 0
                sid_label = str(df_raw.iloc[r, 11]).strip() if cols > 11 else ""
                
                # Extract number from "Surtidor X"
                id_search = re.search(r'\d+', sid_label)
                id_num = int(id_search.group()) if id_search else 0
                
                if id_num > 0:
                    date_list = [d.strip() for d in raw_dates.split(',')] if raw_dates and raw_dates != "nan" else []
                    abs_data.append({
                        "Surtidor": f"Surtidor {id_num}", 
                        "ID": id_num, 
                        "Count": abs_count, 
                        "Dates": date_list
                    })
                            
    except Exception as e:
        st.error(f"Error: {e}")

    ranking_list = []
    for s in range(1, sidebar_limit + 1):
        ranking_list.append({"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)})
    
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
        show_item = False
        if filter_input == "T":
            if item['Count'] > 0: show_item = True
        elif filter_input == "":
            show_item = True
        elif filter_input.isdigit() and int(filter_input) == item['ID']:
            show_item = True
            
        if show_item:
            filtered_abs.append(item)
            total_abs_count += item['Count']

    # Final HTML Table Construction
    rows_html = ""
    for item in filtered_abs:
        dates_str = " | ".join(item['Dates']) if item['Dates'] else "Sin fechas"
        rows_html += f"<tr><td>{item['Surtidor']}</td><td><span class='date-tooltip' title='{dates_str}'>{item['Count']} días</span></td></tr>"

    table_content = f"""<div class="abs-container"><h4 style="margin:0 0 10px 0;">Inasistencias en vista: {total_abs_count}</h4><table class="custom-table"><thead><tr><th>Surtidor</th><th>Ausencias (Hover para fechas)</th></tr></thead><tbody>{rows_html if rows_html else "<tr><td colspan='2'>No hay coincidencias</td></tr>"}</tbody></table></div>"""
    
    st.markdown(table_content, unsafe_allow_html=True)
