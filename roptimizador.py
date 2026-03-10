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
    /* Arial & Blanco Global */
    html, body, [class*="css"], .stText, .stMarkdown, .stTable, .stDataFrame p, h1, h2, h3, span, label, th, td {
        font-family: Arial, Helvetica, sans-serif !important;
        color: #FFFFFF !important;
    }
    .stApp { background-color: #17202A; } 

    /* Matar Toolbar y Textos Fantasmas */
    [data-testid="collapsedControl"], header, .st-emotion-cache-1wbqy5l {
        display: none !important;
        visibility: hidden !important;
    }
    
    [data-testid="stSidebar"] { background-color: #111821 !important; min-width: 350px !important; }
    
    /* Tablas */
    table { color: #FFFFFF !important; width: 100%; border-collapse: collapse; }
    thead tr th { background-color: #212F3C !important; padding: 10px; border: 1px solid #34495E; }
    tbody tr td { border: 1px solid #2C3E50; padding: 8px; }

    .summary-box { background-color: #212F3C; padding: 8px; border-radius: 8px; border: 1px solid #C0392B; }
    .turn-pill { background: #C0392B; color: white !important; padding: 2px 8px; border-radius: 6px; margin: 2px; display: inline-block; font-weight: bold; }
    
    div.stButton > button { background-color: #C0392B !important; color: white !important; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# --- LOGIC: DATA EXTRACTION ---
def parse_smart(text):
    """Extrae datos sin importar el orden de las líneas."""
    data = {}
    # Limpiamos el texto y lo dividimos por líneas o espacios grandes
    tokens = [t.strip() for t in re.split(r'\n|\s{2,}', text) if t.strip()]
    
    i = 0
    while i < len(tokens):
        token = tokens[i]
        # Si el token es un número que coincide con nuestros IDs
        if token.isdigit() and int(token) in ALL_IDS:
            sid = int(token)
            name = "SIN NOMBRE"
            val1 = 0.0
            val2 = 0.0
            
            # Buscamos hacia adelante para llenar los datos de ese ID
            curr = i + 1
            found_data = 0
            while curr < len(tokens) and found_data < 3:
                next_t = tokens[curr]
                # Si nos topamos con otro ID, paramos
                if next_t.isdigit() and int(next_t) in ALL_IDS:
                    break
                
                # Intentamos ver si es número (pedidos/piezas) o nombre
                try:
                    num = float(next_t.replace(',', ''))
                    if found_data == 0: # Si es el primer dato y es número, el nombre se saltó
                         val1 = num
                         found_data = 2 # Saltamos a buscar el segundo número
                    elif found_data >= 1:
                         if found_data == 1: val1 = num
                         else: val2 = num
                         found_data += 1
                except ValueError:
                    # Es texto, por lo tanto es el nombre
                    if found_data == 0:
                        name = next_t.upper()
                        found_data = 1
                curr += 1
            
            data[sid] = {"name": name, "pedidos": val1, "piezas": val2}
            i = curr - 1
        i += 1
    return data

# --- APP STATE ---
if 'ranking' not in st.session_state: st.session_state.ranking = []
if 'scores' not in st.session_state: st.session_state.scores = {}

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Disponibilidad")
    if st.button("🗑️ REINICIAR"):
        st.session_state.clear()
        st.rerun()
    
    active_ids = []
    st.write("---")
    cols = st.columns([1, 1, 1, 1])
    headers = ["ID", "On", "🍴", "Exc"]
    for col, h in zip(cols, headers): col.markdown(f"**{h}**")

    for sid in ALL_IDS:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.markdown(f"ID {sid}")
        on = c2.toggle("", value=True, key=f"on_{sid}", label_visibility="collapsed")
        meal = c3.toggle("", key=f"m_{sid}", label_visibility="collapsed")
        exc = c4.checkbox("", key=f"p_{sid}", label_visibility="collapsed")
        if on and not meal: active_ids.append(sid)

# --- MAIN ---
st.title("🏆 Dashboard de Productividad")

c1, c2 = st.columns(2)
h_in = c1.text_area("1. Acumulado Mes", height=150, placeholder="Pega aquí...")
t_in = c2.text_area("2. Datos Hoy", height=150, placeholder="Pega aquí...")

if st.button("📊 ACTUALIZAR"):
    h_map = parse_smart(h_in)
    t_map = parse_smart(t_in)
    
    combined = []
    new_scores = {}
    
    for sid in ALL_IDS:
        h = h_map.get(sid, {"name": f"ID {sid}", "pedidos": 0, "piezas": 0})
        t = t_map.get(sid, {"name": f"ID {sid}", "pedidos": 0, "piezas": 0})
        
        # El nombre real es el que no sea "ID X" o "SIN NOMBRE"
        final_name = t["name"] if "ID" not in t["name"] and t["name"] != "SIN NOMBRE" else h["name"]
        total_p = h["pedidos"] + t["pedidos"]
        total_i = h["piezas"] + t["piezas"]
        
        new_scores[sid] = total_p
        
        if sid in active_ids or total_p > 0:
            combined.append({
                "ID": sid, "Surtidor": final_name,
                "Total Pedidos": total_p, "Total Piezas": total_i
            })
    
    st.session_state.ranking = sorted(combined, key=lambda x: x['Total Pedidos'], reverse=True)
    st.session_state.scores = new_scores
    st.rerun()

if st.session_state.ranking:
    df = pd.DataFrame(st.session_state.ranking)
    st.table(df[["Surtidor", "Total Pedidos", "Total Piezas"]])

    col_chart, col_eff = st.columns([1.4, 0.6])
    
    with col_chart:
        fig = px.pie(df, values='Total Pedidos', names='Surtidor', hole=0.3,
                     color_discrete_sequence=px.colors.sequential.Reds_r + ['#FFFFFF'])
        fig.update_traces(textinfo='percent+label', textfont_size=15, 
                          marker=dict(line=dict(color='#17202A', width=2)))
        fig.update_layout(height=700, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', 
                          margin=dict(t=0,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_eff:
        st.markdown("### ⚡ Eficiencia (8h)")
        df['Ped/Hr'] = (df['Total Pedidos'] / 8).round(2)
        st.table(df[['Surtidor', 'Ped/Hr']])
