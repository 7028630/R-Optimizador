import streamlit as st
import re
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
HUMAN_IDS = list(range(1, 15)) 
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
    
    .lunch-label { font-size: 1.2rem !important; display: inline-block !important; }
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    .summary-box { background-color: #212F3C; padding: 10px; border-radius: 8px; border-left: 4px solid #C0392B; margin-top: 10px; }
    .summary-row { display: flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px solid #2C3E50; padding: 2px 0; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    .absence-box { background-color: #7B241C; padding: 15px; border-radius: 8px; border-left: 5px solid #E74C3C; margin-top: 10px; margin-bottom: 20px; }
    .absence-item { font-size: 0.9rem; margin-bottom: 5px; border-bottom: 1px solid #922B21; padding-bottom: 3px; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'absences_data' not in st.session_state: st.session_state.absences_data = {}
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ✅Asistencia/Comida🍱")
    if st.button("⌨️ MODO MANUAL" if not st.session_state.manual_mode else "🌐 MODO AUTO"):
        st.session_state.manual_mode = not st.session_state.manual_mode
        st.rerun()
    if st.button("🔄 REINICIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    active_ids = []
    st.write("---")
    h1, h2, h3 = st.columns([2, 1, 1])
    with h1: st.markdown("**ID**")
    with h2: st.markdown("**On**")
    with h3: st.markdown('<span class="lunch-label">🍴</span>', unsafe_allow_html=True)
    
    for sid in ALL_IDS:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.markdown(f"**Surtidor {sid}**")
        with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        if on and not meal and sid in HUMAN_IDS: 
            active_ids.append(sid)

    st.write("---")
    btn_label = "👁️ OCULTAR TURNOS" if st.session_state.show_turns else "🚀 GENERAR TURNOS"
    if st.button(btn_label):
        st.session_state.show_turns = not st.session_state.show_turns
        st.rerun()

    if st.session_state.show_turns and st.session_state.scores and active_ids:
        st.markdown("### ⏭️ Siguientes 20 Turnos")
        temp_scores = st.session_state.scores.copy()
        simulated_turns = []
        turn_counts = {}
        for _ in range(20):
            valid_candidates = {k: v for k, v in temp_scores.items() if k in active_ids}
            if not valid_candidates: break
            next_person = min(valid_candidates, key=valid_candidates.get)
            simulated_turns.append(next_person)
            turn_counts[next_person] = turn_counts.get(next_person, 0) + 1
            temp_scores[next_person] += 1
        st.markdown("".join([f'<span class="turn-pill">S{t}</span>' for t in simulated_turns]), unsafe_allow_html=True)
        summary_html = '<div class="summary-box">'
        sorted_counts = sorted(turn_counts.items(), key=lambda x: x[1], reverse=True)
        for sid, count in sorted_counts:
            summary_html += f'<div class="summary-row"><span>Surtidor {sid}</span> <span>+{count} ped</span></div>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

if st.session_state.manual_mode:
    h_in = st.text_area("1. Histórico Acumulado (Pegar)", height=150)
else:
    st.info("🌐 Alimentando desde la pestaña principal (Mes Actual)")
    h_in = ""

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    absences = {sid: [] for sid in HUMAN_IDS}
    
    def clean_val(v):
        try:
            val_str = str(v).strip().replace(',', '')
            if val_str == "" or val_str == "-" or val_str == "nan": return 0
            return int(float(val_str))
        except: return 0

    if not st.session_state.manual_mode:
        try:
            df_raw = pd.read_csv(SHEET_URL, header=None)
            rows, cols = df_raw.shape
            
            # Identify columns that look like dates (headers usually row 0 or 1)
            # This logic assumes dates are in the header and Surtidor IDs repeat for each day
            for r in range(rows):
                for c in range(cols):
                    cell_val = str(df_raw.iloc[r, c]).strip()
                    if cell_val.isdigit():
                        sid = int(cell_val)
                        if sid in ALL_IDS:
                            if c + 3 < cols:
                                p_val = clean_val(df_raw.iloc[r, c + 2])
                                i_val = clean_val(df_raw.iloc[r, c + 3])
                                data_p[sid] = data_p.get(sid, 0) + p_val
                                data_i[sid] = data_i.get(sid, 0) + i_val
                                
                                # Absence tracking: If ID is human and pedidos are 0
                                if sid in HUMAN_IDS and p_val == 0:
                                    # Try to find a date header in the columns above or nearby
                                    date_label = f"Columna {c}"
                                    absences[sid].append(date_label)
                                    
        except Exception as e:
            st.error(f"Error de conexión: {e}")

    combined = []
    for sid in ALL_IDS:
        p_val, i_val = data_p.get(sid, 0), data_i.get(sid, 0)
        combined.append({"ID": sid, "Surtidor": f"Surtidor {sid}", "Pedidos": p_val, "Piezas": i_val})
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {sid: data_p.get(sid, 0) for sid in ALL_IDS}
    st.session_state.absences_data = {sid: dates for sid, dates in absences.items() if len(dates) > 0}
    st.rerun()

# --- VISUALS ---
if st.session_state.final_ranking:
    st.write("---")
    full_df = pd.DataFrame(st.session_state.final_ranking)
    df_active = full_df[full_df['Pedidos'] > 0].copy()
    
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        fig = px.pie(df_active, values='Pedidos', names='Surtidor', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=11, marker=dict(line=dict(color='#17202A', width=2)))
        fig.update_layout(height=400, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
    with col_table:
        st.markdown("### 🏅 Ranking (IDs)")
        st.table(df_active[["Surtidor", "Pedidos", "Piezas"]])

    # --- AUSENCIAS SECTION ---
    st.write("---")
    st.markdown("### ⚠️ SECCIÓN DE AUSENCIAS")
    
    total_absence_days = sum(len(dates) for dates in st.session_state.absences_data.values())
    
    if total_absence_days > 0:
        st.markdown(f'<div class="absence-box"><h4>Total de inasistencias detectadas: {total_absence_days}</h4>', unsafe_allow_html=True)
        for sid, dates in st.session_state.absences_data.items():
            date_str = ", ".join(dates)
            st.markdown(f'''
                <div class="absence-item">
                    <b>Surtidor {sid}:</b> {len(dates)} día(s) sin pedidos <br>
                    <small style="color: #BDC3C7;">Ubicación en tabla: {date_str}</small>
                </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.success("No se detectaron días con cero pedidos para los Surtidores 1-14.")
