import streamlit as st
import re
import pandas as pd

# --- CONFIGURATION ---
ALL_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

# --- UI STYLE ---
st.set_page_config(page_title="Productividad Surtido", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #EAECEE; color: #1C2833; }
    [data-testid="stSidebar"] { background-color: #17202A !important; min-width: 420px !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: #FFFFFF !important; }
    
    .summary-box { background-color: #212F3C; padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #34495E; color: #FFFFFF !important; }
    .summary-row { display: flex; justify-content: space-between; border-bottom: 1px solid #2C3E50; padding: 3px 0; font-size: 0.9rem !important; }
    .turn-pill { background: #E74C3C; color: white; padding: 4px 10px; border-radius: 8px; margin: 3px; display: inline-block; font-size: 0.85rem; border: 1px solid #566573; font-weight: bold; }
    
    div.stButton > button { background-color: #C0392B !important; color: white !important; border-radius: 8px !important; font-weight: 900 !important; width: 100% !important; }
    </style>
""", unsafe_allow_html=True)

if 'final_ranking' not in st.session_state: st.session_state.final_ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}

# --- SIDEBAR: DISPONIBILIDAD & PRÓXIMOS 20 ---
with st.sidebar:
    st.markdown("### ⚙️ Disponibilidad")
    if st.button("🗑️ REINICIAR TODO"): 
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    st.write("---")
    active_ids = []
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
        
        if on and not meal:
            active_ids.append(sid)

    # --- PRÓXIMOS 20 SECTION ---
    if st.session_state.scores and active_ids:
        st.write("---")
        st.markdown("#### 🔄 Proyección: Siguientes 20")
        
        # Simulation of the next 20 turns based on current ranking scores
        ts = st.session_state.scores.copy()
        turns, counts = [], {}
        
        for _ in range(20):
            # Only consider active IDs for the projection
            valid_scores = {k: v for k, v in ts.items() if k in active_ids}
            if not valid_scores: break
            
            next_id = min(valid_scores, key=valid_scores.get)
            turns.append(next_id)
            counts[next_id] = counts.get(next_id, 0) + 1
            ts[next_id] += 1
            
        st.markdown("".join([f'<span class="turn-pill">{t}</span>' for t in turns]), unsafe_allow_html=True)
        
        summary_html = '<div class="summary-box"><b>Turnos a asignar:</b>'
        for sid, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            summary_html += f'<div class="summary-row"><span>ID {sid}</span> <span>{count} pedidos</span></div>'
        st.markdown(summary_html + '</div>', unsafe_allow_html=True)

# --- MAIN CONTENT ---
st.title("🏆 Ranking y Proyección de Carga")

c1, c2 = st.columns(2)
with c1:
    h_in = st.text_area("1. Cuadro de productividad de cada día del mes", height=150, 
                        placeholder="Pega aquí los datos acumulados del mes...")
with c2:
    t_in = st.text_area("2. Totales del día actual", height=150, 
                        placeholder="Pega aquí los totales de hoy...")

if st.button("📊 ACTUALIZAR RANKING Y TURNOS"):
    pat = r"(\d+)\s+([A-Z\s\.\-_]+?)\s+(\d+)"
    names_map = {}
    historical_data = {}
    
    if h_in.strip():
        matches = re.findall(pat, h_in)
        for sid_raw, name, count in matches:
            sid = int(sid_raw)
            historical_data[sid] = historical_data.get(sid, 0) + int(count)
            names_map[sid] = name.strip()

    today_data = {}
    if t_in.strip():
        matches_today = re.findall(pat, t_in)
        for sid_raw, name, count in matches_today:
            sid = int(sid_raw)
            today_data[sid] = int(count)
            if sid not in names_map: names_map[sid] = name.strip()

    # Consolidate and prepare scores for the Sidebar Projection
    combined = []
    current_scores = {}
    
    for sid in ALL_IDS:
        h_val = historical_data.get(sid, 0)
        t_val = today_data.get(sid, 0)
        total = h_val + t_val
        
        # Store score for the "Next 20" logic
        current_scores[sid] = total
        
        # Only add to the visible table if they are in the data or active
        if sid in active_ids or total > 0:
            combined.append({
                "ID": sid,
                "Surtidor": names_map.get(sid, f"ID {sid}"),
                "Histórico": h_val,
                "Hoy": t_val,
                "Total": total
            })
    
    st.session_state.final_ranking = sorted(combined, key=lambda x: x['Total'], reverse=True)
    st.session_state.scores = current_scores
    st.rerun()

# --- DISPLAY RANKING TABLE ---
if st.session_state.final_ranking:
    st.write("---")
    df = pd.DataFrame(st.session_state.final_ranking)
    df.index = range(1, len(df) + 1)
    df.index.name = "Puesto"
    df['ID'] = df['ID'].astype(str)

    st.dataframe(
        df, 
        use_container_width=True,
        column_config={
            "Total": st.column_config.NumberColumn(format="%d 📦"),
            "Histórico": st.column_config.NumberColumn(format="%d"),
            "Hoy": st.column_config.NumberColumn(format="%d"),
        }
    )
    
    top_performer = st.session_state.final_ranking[0]
    st.success(f"🥇 **Líder:** {top_performer['Surtidor']} con **{top_performer['Total']}** pedidos.")
else:
    st.info("Pega los datos y actualiza para ver el ranking y la proyección de turnos.")
