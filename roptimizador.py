import streamlit as st
import re
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
# This URL defaults to the FIRST TAB (index 0) of the spreadsheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# --- UI STYLE ---
@@ -92,25 +93,27 @@
if st.session_state.manual_mode:
h_in = st.text_area("1. Histórico Acumulado (Pegar)", height=150)
else:
    st.info("🌐 Alimentando desde Google Sheets")
    st.info("🌐 Alimentando desde la pestaña principal (Mes Actual)")
h_in = ""

if st.button(" ✳️ ACTUALIZAR PANEL"):
data_p, data_i = {}, {}
def clean_val(v):
try:
val_str = str(v).strip().replace(',', '')
            if val_str == "" or val_str == "-": return 0
            if val_str == "" or val_str == "-" or val_str == "nan": return 0
return int(float(val_str))
except: return 0

if not st.session_state.manual_mode:
try:
            # Reads the first sheet in the book
df_raw = pd.read_csv(SHEET_URL, header=None)
rows, cols = df_raw.shape
            # Start scanning from index 4 (Column E)
            
            # Scanning logic: Look for IDs in any column and grab Peds/Pzas
for r in range(rows):
                for c in range(4, cols):
                for c in range(cols):
cell_val = str(df_raw.iloc[r, c]).strip()
if cell_val.isdigit():
sid = int(cell_val)
@@ -120,43 +123,44 @@
i_val = clean_val(df_raw.iloc[r, c + 3])
data_p[sid] = data_p.get(sid, 0) + p_val
data_i[sid] = data_i.get(sid, 0) + i_val
        except: pass
        except Exception as e:
            st.error(f"Error de conexión con Google Sheets: {e}")

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
