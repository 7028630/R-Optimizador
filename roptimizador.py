import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
ALL_IDS = list(range(1, 22)) 
# Using the CSV export link provided
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_O8vDPqBIMH1m7VrJ1faviWIoM5fX5TmYb597wzTXUc/export?format=csv"

# [UI STYLE SECTION REMAINS UNCHANGED]
st.set_page_config(page_title="Productividad Surtido", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # Your existing CSS

# [SIDEBAR SECTION REMAINS UNCHANGED]

# --- MAIN CONTENT ---
st.title("📦 Panel de Productividad")

# --- MAIN CONTENT --- (Inside the st.button(" ✳️ ACTUALIZAR PANEL") block)
if st.button(" ✳️ ACTUALIZAR PANEL"):
    data_p, data_i = {}, {}
    abs_data = []
@@ -27,11 +10,10 @@ def clean_val(v):
        except: return 0

    try:
        # Load the sheet
        df_raw = pd.read_csv(SHEET_URL, header=None)
        rows, cols = df_raw.shape

        # 1. PARSE PRODUCTIVITY (The main grid)
        # 1. Main Productivity Grid (Original Logic)
        for r in range(rows):
            for c in range(cols):
                cell_val = str(df_raw.iloc[r, c]).strip()
@@ -43,68 +25,37 @@ def clean_val(v):
                        data_p[sid] = data_p.get(sid, 0) + p_val
                        data_i[sid] = data_i.get(sid, 0) + i_val

        # 2. PARSE AUSENCIAS (Targeting J2:L23)
        # In pandas: Column J=9, K=10, L=11. Rows 2-23 are indices 1-22.
        for r in range(1, 23):
        # 2. AUSENCIAS Table Logic (Feeding from J2:L23)
        # We start at r=2 (index 2) to skip your headers in row 1
        for r in range(2, 23): 
            if r < rows:
                # Column J (Index 9) = Dates
                # Column K (Index 10) = Amount of Ausencias
                # Column L (Index 11) = ID/Name
                # J=9 (Dates), K=10 (Count), L=11 (ID)
                raw_dates = str(df_raw.iloc[r, 9]).strip() if cols > 9 else ""
                abs_count = clean_val(df_raw.iloc[r, 10]) if cols > 10 else 0
                sid_val = str(df_raw.iloc[r, 11]).strip() if cols > 11 else ""
                sid_label = str(df_raw.iloc[r, 11]).strip() if cols > 11 else ""

                # Extract ID number from string (e.g., "Surtidor 1" -> 1)
                id_match = re.search(r'\d+', sid_val)
                sid_int = int(id_match.group()) if id_match else 0
                # Get the ID number (Surtidor 1 -> 1)
                id_num = int(re.search(r'\d+', sid_label).group()) if re.search(r'\d+', sid_label) else 0

                if sid_int > 0:
                    # Split dates if they are comma-separated for the tooltip
                if id_num > 0:
                    # Split the dates by comma for the hover effect
                    date_list = [d.strip() for d in raw_dates.split(',')] if raw_dates else []
                    abs_data.append({
                        "Surtidor": f"Surtidor {sid_int}", 
                        "ID": sid_int, 
                        "Surtidor": f"Surtidor {id_num}", 
                        "ID": id_num, 
                        "Count": abs_count, 
                        "Dates": date_list
                    })

        # Update Session State
        ranking_list = [{"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)} for s in range(1, sidebar_limit + 1)]
        # --- Update Session State ---
        ranking_list = []
        for s in range(1, sidebar_limit + 1):
            ranking_list.append({"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)})
        
        st.session_state.final_ranking = sorted(ranking_list, key=lambda x: x['Pedidos'], reverse=True)
        st.session_state.scores = {s: data_p.get(s, 0) for s in ALL_IDS}
        st.session_state.abs_list = abs_data
        st.rerun()

    except Exception as e:
        st.error(f"Error updating: {e}")

# --- VISUALS ---
if st.session_state.final_ranking:
    # [RANKING TABLE & PIE CHART REMAINS UNCHANGED]

    # --- AUSENCIAS SECTION ---
    st.write("---")
    st.markdown("### ⚠️ AUSENCIAS")
    
    filter_input = st.text_input("Filtro (ID o 'T' para ausentes):", key="abs_filter").strip().upper()
    
    rows_html = ""
    total_abs_count = 0
    for item in st.session_state.abs_list:
        show = (filter_input == "T" and item['Count'] > 0) or (filter_input == "") or (filter_input.isdigit() and int(filter_input) == item['ID'])
        
        if show:
            total_abs_count += item['Count']
            dates_str = " | ".join(item['Dates']) if item['Dates'] and item['Dates'] != [""] else "Sin fechas"
            rows_html += f"<tr><td>{item['Surtidor']}</td><td><span class='date-tooltip' title='{dates_str}'>{item['Count']} días</span></td></tr>"

    table_content = f"""
    <div class="abs-container">
        <h4 style="margin:0 0 10px 0;">Inasistencias en vista: {total_abs_count}</h4>
        <table class="custom-table">
            <thead><tr><th>Surtidor</th><th>Ausencias (Hover para fechas)</th></tr></thead>
            <tbody>{rows_html if rows_html else "<tr><td colspan='2'>No hay coincidencias</td></tr>"}</tbody>
        </table>
    </div>"""
    
    st.markdown(table_content, unsafe_allow_html=True)
        st.error(f"Error: {e}")
