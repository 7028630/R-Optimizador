import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
HUMAN_IDS = list(range(1, 15)) 
# Tab-specific URL (gid=1115153798)
ABSENCIAS_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv&gid=1115153798"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Global Styles */
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; }
    header, [data-testid="stHeader"] { background-color: #17202A !important; }
    [data-testid="stSidebar"] { background-color: #111821 !important; }
    
    /* FIX: REMOVE THE WHITE CODE-LIKE LETTERS (TOOLTIPS) ON HOVER */
    div[data-testid="stSidebarCollapseButton"] button div {
        display: none !important;
    }
    div[data-testid="stSidebarCollapseButton"] button:after {
        content: "Ocultar 👁️";
        font-size: 14px;
        color: white;
        font-weight: bold;
    }

    .lunch-label { font-size: 1.2rem !important; display: inline-block !important; visibility: visible !important; }
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    .summary-box { background-color: #212F3C; padding: 10px; border-radius: 8px; border-left: 4px solid #C0392B; margin-top: 10px; }
    .summary-row { display: flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px solid #2C3E50; padding: 2px 0; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    .absence-box { background-color: #7B241C; padding: 15px; border-radius: 8px; border-left: 5px solid #E74C3C; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
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
    
    # Strictly IDs 1-14
    for sid in HUMAN_IDS:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1: st.markdown(f"**Surtidor {sid}**")
        with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        if on and not meal: 
            active_ids.append(sid)

    st.write("---")
    
    btn_label = "👁️ OCULTAR TURNOS" if st.session_state.show_turns else "🚀 GENERAR TURNOS"
    if st.button(btn_label):
        st.session_state.show_turns = not st.session_state.show_turns
        st.rerun()

    if st.session_state.show_turns and st.session_state.scores and active_ids:
        st.markdown("### ⏭️ Siguientes 20 Turnos")
        temp_scores = {k: v for k, v in st.session_state.scores.items() if k in active_ids}
        simulated_turns = []
        turn_counts = {}
        
        for _ in range(20):
            if not temp_scores: break
            next_person = min(temp_scores, key=temp_scores.get)
            simulated_turns.append(next_person)
            turn_counts[next_person] = turn_counts.get(next_person, 0) + 1
            temp_scores[next_person] += 1
            
        st.markdown("".join([f'<span class="turn-pill">S{t}</span>' for t in simulated_turns]), unsafe_allow_html=True)
        summary_html = '<div class="summary-box"><b>Distribución:</b><br>'
        for sid, count in sorted(turn_counts.items(), key=lambda x: x[1], reverse=True):
            summary_html += f'<div class="summary-row"><span>Surtidor {sid}</span> <span>+{count} ped</span></div>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

def clean_val(v):
    try:
        val_str = str(v).strip().replace(',', '')
        if val_str in ["", "-", "nan", "None"]: return 0
        return int(float(val_str))
    except: return 0

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    if not st.session_state.manual_mode:
        try:
            df_raw = pd.read_csv(SHEET_URL, header=None)
            for r in range(len(df_raw)):
                for c in range(len(df_raw.columns)):
                    cell = str(df_raw.iloc[r, c]).strip()
                    if cell.isdigit() and int(cell) in HUMAN_IDS:
                        sid = int(cell)
                        data_p[sid] = clean_val(df_raw.iloc[r, c + 2])
                        data_i[sid] = clean_val(df_raw.iloc[r, c + 3])
        except Exception as e: st.error(f"Error: {e}")

    st.session_state.final_ranking = sorted(
        [{"ID": i, "Surtidor": f"Surtidor {i}", "Pedidos": data_p.get(i,0), "Piezas": data_i.get(i,0)} for i in HUMAN_IDS],
        key=lambda x: x['Pedidos'], reverse=True
    )
    st.session_state.scores = {i: data_p.get(i,0) for i in HUMAN_IDS}
    st.rerun()

# --- VISUALS & AUSENCIAS ---
if st.session_state.final_ranking:
    full_df = pd.DataFrame(st.session_state.final_ranking)
    df_active = full_df[full_df['Pedidos'] > 0]
    
    col_chart, col_table = st.columns([1, 1])
    with col_chart:
        if not df_active.empty:
            fig = px.pie(df_active, values='Pedidos', names='Surtidor', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r)
            st.plotly_chart(fig, use_container_width=True)
    with col_table:
        st.markdown("### 🏅 Ranking (IDs 1-14)")
        st.table(df_active[["Surtidor", "Pedidos", "Piezas"]])

    st.write("---")
    st.markdown("### ⚠️ AUSENCIAS")
    try:
        # Load the specific tab for Ausencias
        df_abs = pd.read_csv(ABSENCIAS_URL, header=None)
        absents = []
        for r in range(len(df_abs)):
            for c in range(len(df_abs.columns)):
                cell = str(df_abs.iloc[r, c]).strip()
                if cell.isdigit() and int(cell) in HUMAN_IDS:
                    if clean_val(df_abs.iloc[r, c + 2]) == 0:
                        absents.append(f"Surtidor {cell}")
        
        if absents:
            st.markdown(f'<div class="absence-box"><b>Faltantes hoy (1-14):</b><br>{", ".join(sorted(list(set(absents))))}</div>', unsafe_allow_html=True)
        else:
            st.success("Asistencia completa (1-14).")
    except:
        st.error("Error cargando pestaña de Ausencias.")
