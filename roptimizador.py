import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
HUMAN_IDS = list(range(1, 15)) # Strictly 1-14
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
    
    .custom-table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; margin-top: 10px; }
    .custom-table thead tr th { color: #FFFFFF !important; background-color: #212F3C !important; border-bottom: 2px solid #C0392B !important; padding: 12px; text-align: left; }
    .custom-table tbody tr td { color: #FFFFFF !important; border-bottom: 1px solid #2C3E50 !important; padding: 10px; }
    
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block; font-size: 0.8rem; font-weight: bold; }
    div.stButton > button { background-color: #C0392B !important; color: #FFFFFF !important; font-weight: bold !important; width: 100%; border: none; }
    
    /* Hover tooltip style */
    .date-tooltip { cursor: help; border-bottom: 2px dotted #E74C3C; color: #E74C3C; font-weight: bold; padding: 2px 5px; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}
if 'abs_list' not in st.session_state: st.session_state.abs_list = []
if 'manual_mode' not in st.session_state: st.session_state.manual_mode = False
if 'show_turns' not in st.session_state: st.session_state.show_turns = False

# --- SIDEBAR ---
with st.sidebar:
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
        # ONLY show toggle for Human IDs (1-14)
        if sid in HUMAN_IDS:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1: st.markdown(f"**Surtidor {sid}**")
            with col2: on = st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
            with col3: meal = st.toggle("", key=f"m_{sid}", label_visibility="collapsed")
            if on and not meal: active_ids.append(sid)
        else:
            # Maintain state keys for 15-21 but don't render UI
            st.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
            st.toggle("", key=f"m_{sid}", label_visibility="collapsed")

    st.write("---")
    btn_label = "👁️ OCULTAR TURNOS" if st.session_state.show_turns else "🚀 GENERAR TURNOS"
    if st.button(btn_label):
        st.session_state.show_turns = not st.session_state.show_turns
        st.rerun()

    if st.session_state.show_turns and st.session_state.scores and active_ids:
        st.markdown("### ⏭️ Siguientes 20 Turnos")
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
            val_str = str(v).strip().replace(',', '')
            return int(float(val_str)) if val_str not in ["", "-", "nan"] else 0
        except: return 0

    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
        rows, cols = df_raw.shape
        # Temporary storage to group dates per surtidor for the table
        temp_abs = {sid: [] for sid in HUMAN_IDS}

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
                        
                        # Absence Tracking for 1-14
                        if sid in HUMAN_IDS and p_val == 0:
                            date_val = str(df_raw.iloc[r, 5]).strip() if cols > 5 else "Fecha N/A"
                            temp_abs[sid].append(date_val)
                            
        # Flatten temp_abs into a list for easier filtering later
        for sid, dates in temp_abs.items():
            abs_data.append({"Surtidor": f"Surtidor {sid}", "ID": sid, "Count": len(dates), "Dates": dates})
                            
    except Exception as e:
        st.error(f"Error: {e}")

    st.session_state.final_ranking = sorted([{"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)} for s in ALL_IDS], key=lambda x: x['Pedidos'], reverse=True)
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
    st.markdown("### ⚠️ AUSENCIAS (Surtidores 1-14)")
    
    # FILTER BAR
    search_query = st.text_input("🔍 Filtrar por Surtidor o Fecha:", placeholder="Ej: 14 o 25/03...")
    
    filtered_abs = []
    total_abs_count = 0
    
    for item in st.session_state.abs_list:
        dates_str = " | ".join(item['Dates'])
        # Check if query matches surtidor name or any date in the list
        if search_query.lower() in item['Surtidor'].lower() or search_query.lower() in dates_str.lower():
            filtered_abs.append(item)
            total_abs_count += item['Count']

    abs_rows_html = ""
    for item in filtered_abs:
        date_tooltip = " | ".join(item['Dates']) if item['Dates'] else "Sin ausencias"
        abs_rows_html += f"""
            <tr>
                <td>{item['Surtidor']}</td>
                <td><span class="date-tooltip" title="{date_tooltip}">{item['Count']} días</span></td>
            </tr>
        """
    
    st.markdown(f"""
    <div style="background-color: #212F3C; padding: 20px; border-radius: 10px; border-left: 5px solid #C0392B;">
        <h4 style="margin-top:0;">Inasistencias detectadas: {total_abs_count}</h4>
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Surtidor</th>
                    <th>Días con 0 Pedidos (Pasa el mouse para ver fechas)</th>
                </tr>
            </thead>
            <tbody>
                {abs_rows_html if filtered_abs else '<tr><td colspan="2">No se encontraron resultados.</td></tr>'}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
