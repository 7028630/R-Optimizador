import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
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

    if p_val in [14, 8, 1, 2]: return p_val
    if (3 <= p_val <= 7 or p_val == 9) and now >= d1245: return 16
    if (p_val == 10 or p_val == 11) and now >= d1500: return 18
    if p_val == 12 and now >= d1600: return 19
    if 3 <= p_val <= 9: return 3
    return p_val

def parse_pending(raw_text):
    if not raw_text: return []
    lines = raw_text.strip().split('\n')
    orders = []
    
    for line in lines:
        if "#N/A" in line or "CANCELADO" in line: continue
        
        # This regex now looks for numbers separated by any amount of whitespace (tabs/spaces)
        # Group 1: Order (64...) | Group 2: Priority | Group 3: Items
        match = re.search(r"(64\d{4})\s+(\d{1,2})\s+(\d+)", line)
        
        # If the above fails (because there are no spaces), try the "stuck" version
        if not match:
            match = re.search(r"(64\d{4})(\d{1,2})(\d+)", line)

        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            
            # If a 2-digit priority isn't in our list (like 18), 
            # we check if the 1st digit is a valid priority.
            if p_int not in PRIORITY_NAMES and len(p_raw) == 2:
                p_int = int(p_raw[0])
                items = p_raw[1] + items

            if p_int in PRIORITY_NAMES:
                orders.append({
                    "ID": oid, 
                    "LiveP": get_live_priority(p_int), 
                    "Items": int(items), 
                    "RawP": p_int,
                    "Name": PRIORITY_NAMES.get(p_int)
                })
            
    return sorted(orders, key=lambda x: (x['LiveP'], -x['Items']))

# --- UI ---
st.set_page_config(page_title="Warehouse Ops", layout="wide")

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

# --- SIDEBAR ---
with st.sidebar:
    st.header("Team Management")
    if st.button("🔄 CLEAR SESSION"): 
        st.rerun()
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
with col3: o_in = st.text_area("3. Pending Orders", height=150)

if st.button("💊 GENERATE ROTATION"):
    if not o_in:
        st.error("Paste data in Column 3.")
    else:
        # Rotation Math
        pat = r"(\d+)[A-Z\s\.]+(\d+)"
        h_blocks = []
        for line in h_in.strip().split('\n'):
            m = re.findall(pat, line)
            if m: h_blocks.append({int(k): int(v) for k, v in m})
        
        t_m = re.findall(pat, t_in)
        t_counts = {int(k): int(v) for k, v in t_m if int(k) in active_ids}
        
        pending = parse_pending(o_in)

        scores = {}
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        avg = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        top = 0
        
        for idx in active_ids:
            is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            if idx in pardon_ids or is_new:
                scores[idx] = int(avg / len(ALL_IDS)) + t_counts.get(idx, 0) if avg > 0 else t_counts.get(idx, 0)
            else:
                scores[idx] = h_sum + t_counts.get(idx, 0)
                top = max(top, scores[idx])
        
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids: scores[idx] = top + 5

        # Display Result
        st.write("---")
        if not pending:
            st.warning("Still no orders detected. Please ensure you are copying the ID, Priority, and Items columns.")
        else:
            last_id = None
            for i, order in enumerate(pending[:30]):
                rotation = sorted(scores.items(), key=lambda x: x[1])
                best_id = rotation[0][0]
                if best_id == last_id and len(rotation) > 1:
                    best_id = rotation[1][0]
                
                scores[best_id] += 1
                last_id = best_id
                
                with st.container():
                    c_chk, c_crd = st.columns([1, 20])
                    with c_chk: done = st.checkbox("", key=f"ck_{order['ID']}_{i}")
                    if not done:
                        with c_crd:
                            st.markdown(f"""
                            <div class="assignment-card">
                                <b style="color:#990000; font-size:18px;">ID {best_id}</b> ⮕ 
                                <b>{order['ID']}</b> | {order['Name']} | {order['Items']} Items
                            </div>
                            """, unsafe_allow_html=True)
