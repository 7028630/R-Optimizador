# --- MAIN CONTENT --- (Inside the st.button(" ✳️ ACTUALIZAR PANEL") block)
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

        # 1. Main Productivity Grid (Original Logic)
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
        
        # 2. AUSENCIAS Table Logic (Feeding from J2:L23)
        # We start at r=2 (index 2) to skip your headers in row 1
        for r in range(2, 23): 
            if r < rows:
                # J=9 (Dates), K=10 (Count), L=11 (ID)
                raw_dates = str(df_raw.iloc[r, 9]).strip() if cols > 9 else ""
                abs_count = clean_val(df_raw.iloc[r, 10]) if cols > 10 else 0
                sid_label = str(df_raw.iloc[r, 11]).strip() if cols > 11 else ""
                
                # Get the ID number (Surtidor 1 -> 1)
                id_num = int(re.search(r'\d+', sid_label).group()) if re.search(r'\d+', sid_label) else 0
                
                if id_num > 0:
                    # Split the dates by comma for the hover effect
                    date_list = [d.strip() for d in raw_dates.split(',')] if raw_dates else []
                    abs_data.append({
                        "Surtidor": f"Surtidor {id_num}", 
                        "ID": id_num, 
                        "Count": abs_count, 
                        "Dates": date_list
                    })

        # --- Update Session State ---
        ranking_list = []
        for s in range(1, sidebar_limit + 1):
            ranking_list.append({"ID": s, "Surtidor": f"Surtidor {s}", "Pedidos": data_p.get(s,0), "Piezas": data_i.get(s,0)})
        
        st.session_state.final_ranking = sorted(ranking_list, key=lambda x: x['Pedidos'], reverse=True)
        st.session_state.scores = {s: data_p.get(s, 0) for s in ALL_IDS}
        st.session_state.abs_list = abs_data
        st.rerun()
                            
    except Exception as e:
        st.error(f"Error: {e}")
