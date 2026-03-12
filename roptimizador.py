import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

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
    [data-testid="stSidebarNav"] + div, button[title="Collapse sidebar"], [data-testid="collapsedControl"] {
        display: none !important; visibility: hidden !important;
    }
    .lunch-label { font-size: 1.2rem !important; display: inline-block !important; visibility: visible !important; }
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; }
    tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    .summary-box { background-color: #212F3C; padding: 10px; border-radius: 8px; border-left: 4px solid #C0392B; margin-top: 10px; }
    .summary-row { display: flex; justify-content: space-between; font-size: 0.85rem; border-bottom: 1px solid #2C3E50; padding: 2px 0; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; }
    .stats-container { background-color: #212F3C; padding: 15px; border-radius: 10px; border: 1px solid #C0392B; text-align: center; margin-top: -20px; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ✅Asistencia/Comida🍱")
    if st.button("⌨️ MODO MANUAL (PEGAR)" if not st.session_state.manual_mode else "🌐 MODO AUTO (SHEET)"):
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
        if on and not meal: active_ids.append(sid)

    st.write("---")
    if st.button("🚀 GENERAR TURNOS"):
        st.session_state.show_turns = True

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
        summary_html = '<div class="summary-box"><b>Distribución:</b><br>'
        sorted_counts = sorted(turn_counts.items(), key=lambda x: x[1], reverse=True)
        for sid, count in sorted_counts:
            summary_html += f'<div class="summary-row"><span>Surtidor {sid}</span> <span>+{count} ped</span></div>'
        summary_html += '</div>'
        st.markdown(summary_html, unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("📦💊 Panel de Productividad 💊📦")

if st.session_state.manual_mode:
    h_in = st.text_area("1. Histórico Acumulado (Pegar)", height=150)
else:
    st.info("🌐 Alimentando desde Google Sheets (Multi-Tabla)")
    h_in = ""

if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    def clean_val(v):
        try:
            val_str = str(v).strip().replace(',', '')
            if val_str == "" or val_str == "-": return 0
            return int(float(val_str))
        except: return 0

    if not st.session_state.manual_mode:
        try:
            df_raw = pd.read_csv(SHEET_URL, header=None)
            rows, cols = df_raw.shape
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
        except: pass

    if st.session_state.manual_mode and h_in.strip():
        pat = r"(\d+)\s+([A-Za-z\s\.\-_]+|[0\s\-]+)?\s*([\d\.,]+)\s+([\d\.,\-]+)"
        matches = re.findall(pat, h_in)
        for sid_raw, _, ped, pza in matches:
            sid = int(sid_raw)
            data_p[sid] = data_p.get(sid, 0) + clean_val(ped)
            data_i[sid] = data_i.get(sid, 0) + clean_val(pza)

    combined = []
    for sid in ALL_IDS:
        p_val, i_val = data_p.get(sid, 0), data_i.get(sid, 0)
        if p_val > 0 or i_val > 0:
            combined.append({"ID": sid, "Surtidor": f"Surtidor {sid}", "Pedidos": p_val, "Piezas": i_val})
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Pedidos'], reverse=True)
    st.session_state.scores = {sid: data_p.get(sid, 0) for sid in ALL_IDS}
    st.session_state.show_turns = False
    st.rerun()

# --- VISUALS ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1)
    col_chart, col_table = st.columns([1.3, 0.7])
    with col_chart:
        fig = px.pie(df, values='Pedidos', names='Surtidor', hole=.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        fig.update_traces(textinfo='percent+label', textfont_size=14, marker=dict(line=dict(color='#17202A', width=2)))
        fig.update_layout(height=850, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f'<div class="stats-container"><span style="font-size: 0.9rem; color: #BDC3C7;">Balance de Carga (Pedidos)</span><br><span style="font-size: 1.8rem; font-weight: bold; color: #FFFFFF;">σ {df["Pedidos"].std():.2f}</span><br><span style="font-size: 0.8rem; color: #E74C3C;">Promedio: {df["Pedidos"].mean():.1f}</span></div>', unsafe_allow_html=True)
    with col_table:
        st.markdown("### 🏅 Ranking (IDs)")
        st.table(df[["Surtidor", "Pedidos", "Piezas"]])
        st.markdown("### ⚡ Eficiencia")
        df_eff = df.copy()
        df_eff['P/Hr'] = (df_eff['Pedidos'] / 8).round(1)
        st.table(df_eff[['Surtidor', 'P/Hr']])
