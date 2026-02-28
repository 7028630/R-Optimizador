import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & PRIORITY MAP ---
ALL_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]

PRIORITY_NAMES = {
    1: "Local Urgente (1)", 2: "Local Urgente (2)",
    3: "Apodaca", 4: "Guadalupe", 5: "Santa Catarina",
    6: "Solidaridad", 7: "Unidad", 8: "Sur Foráneo", 9: "Sur",
    10: "Foráneo Urgente", 11: "Foráneo", 12: "Torreón",
    14: "Saltillo", 16: "Local Desp. Corte",
    17: "Foráneo Urg. Desp. Corte", 18: "Foráneo Desp. Corte", 19: "Torreón Desp. Corte"
}

def get_live_priority(p_val):
    now = datetime.now().time()
    d1245 = datetime.strptime("12:45", "%H:%M").time()
    d1500 = datetime.strptime("15:00", "%H:%M").time()
    d1600 = datetime.strptime("16:00", "%H:%M").time()

    if p_val == 14 or p_val == 8 or p_val <= 2:
        return p_val
    if (3 <= p_val <= 7 or p_val == 9) and now >= d1245:
        return 16
    if (p_val == 10 or p_val == 11) and now >= d1500:
        return 18
    if p_val == 12 and now >= d1600:
        return 19
    # Group 3-9 as same importance level if before deadline
    if 3 <= p_val <= 9:
        return 3 
    return p_val

def parse_pending(raw_text):
    if not raw_text: return []
    # Split by the Order ID prefix "64" to separate stuck lines
    raw_text = raw_text.replace("64", "\n64")
    lines = raw_text.strip().split('\n')
    orders = []
    
    for line in lines:
        if "#N/A" in line or "CANCELADO" in line or not line.strip(): continue
        
        # New Regex logic: 
        # 1. Finds the 6-digit Order ID starting with 64
        # 2. Captures the next 1 or 2 digits (Priority)
        # 3. Captures the next digits (Items)
        match = re.search(r"(64\d{4})(\d{1,2}?)(\d{1,4})", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            live_p = get_live_priority(p_int)
            orders.append({
                "ID": oid, 
                "LiveP": live_p, 
                "Items": int(items), 
                "RawP": p_int,
                "Name": PRIORITY_NAMES.get(p_int, f"Type {p_int}")
            })
            
    return sorted(orders, key=lambda x: (x['LiveP'], -x['Items']))

# --- UI ---
st.set_page_config(page_title="Warehouse Dispatch", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .assignment-card { 
        background: white; padding: 12px; border-left: 10px solid #990000; 
        border-radius: 6px; margin-bottom: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Smart Dispatch Rotation")

# --- SIDEBAR: SIMPLE PERSONNEL ---
with st.sidebar:
    st.header("Team Management")
    if st.button("CLEAR ALL"): st.cache_data.clear(); st.rerun()
    st.write("---")
    
    active_ids = []
    pardon_ids = []
    for i in ALL_IDS:
        c1, c2, c3 = st.columns([2,1,1])
        with c1: on = st.toggle(f"ID {i}", value=True, key=f"on_{i}")
        with c2: meal = st.toggle("🍴", key=f"m_{i}")
        with c3: pdr = st.checkbox("OVR", key=f"p_{i}")
        
        if on and not meal: active_ids.append(i)
        if pdr: pardon_ids.append(i)

# --- INPUTS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("1. Historical Data", height=150)
with col2: t_in = st.text_area("2. Today's Totals", height=150)
with col3: o_in = st.text_area("3. Pending Orders (Paste Here)", height=150)

if st.button("💊 RUN ROTATION"):
    if not o_in:
        st.error("Column 3 is empty.")
    else:
        # Parse Personnel Data
        pat = r"(\d+)[A-Z\s\.]+(\d+)"
        h_blocks = []
        for line in h_in.strip().split('\n'):
            matches = re.findall(pat, line)
            if matches: h_blocks.append({int(k): int(v) for k, v in matches})
        
        t_matches = re.findall(pat, t_in)
        t_counts = {int(k): int(v) for k, v in t_matches if int(k) in active_ids}
        
        # Parse Orders
        pending = parse_pending(o_in)

        # Calculate Scores
        scores = {}
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        avg_score = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        top_score = 0
        
        for idx in active_ids:
            is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            current = t_counts.get(idx, 0)
            
            if idx in pardon_ids or is_new:
                scores[idx] = int(avg_score / len(ALL_IDS)) + current if avg_score > 0 else current
            else:
                scores[idx] = h_sum + current
                top_score = max(top_score, scores[idx])
        
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids: scores[idx] = top_score + 5

        # Display Results
        st.write("---")
        st.subheader(f"Current Priority Queue ({datetime.now().strftime('%H:%M')})")
        
        if not pending:
            st.warning("No orders detected. Try pasting the data again.")
        else:
            last_id = None
            for i, order in enumerate(pending[:20]):
                rotation = sorted(scores.items(), key=lambda x: x[1])
                if not rotation: break
                best_id = rotation[0][0]
                if best_id == last_id and len(rotation) > 1:
                    best_id = rotation[1][0]
                
                scores[best_id] += 1
                last_id = best_id
                
                with st.container():
                    c_check, c_card = st.columns([1, 15])
                    with c_check:
                        done = st.checkbox("", key=f"d_{order['ID']}_{i}")
                    if not done:
                        with c_card:
                            st.markdown(f"""
                            <div class="assignment-card">
                                <b style="color:#990000; font-size:19px;">ID {best_id}</b> ⮕ 
                                Order: <b>{order['ID']}</b> | {order['Name']} | {order['Items']} Items
                            </div>
                            """, unsafe_allow_html=True)

st.write("---")
st.caption("Auto-Rules: Locals (3-9) -> Corte @ 12:45 | Foráneos (10-11) -> Corte @ 15:00 | Torreón -> Corte @ 16:00")
