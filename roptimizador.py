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
    # 12:45 PM Deadline
    d1245 = datetime.strptime("12:45", "%H:%M").time()
    # 03:00 PM Deadline
    d1500 = datetime.strptime("15:00", "%H:%M").time()
    # 04:00 PM Deadline
    d1600 = datetime.strptime("16:00", "%H:%M").time()

    # Exceptions: Saltillo (14) and Sur Foráneo (8) NEVER change
    if p_val == 14 or p_val == 8 or p_val <= 2:
        return p_val
    
    # Rule 1: Locals (3-7, 9) -> 16 after 12:45
    if (3 <= p_val <= 7 or p_val == 9) and now >= d1245:
        return 16
    
    # Rule 2: Foráneos (10-11) -> 18 after 15:00
    if (p_val == 10 or p_val == 11) and now >= d1500:
        return 18
        
    # Rule 3: Torreón (12) -> 19 after 16:00
    if p_val == 12 and now >= d1600:
        return 19
        
    return p_val

def parse_pending(raw_text):
    if not raw_text: return []
    lines = raw_text.strip().split('\n')
    orders = []
    for line in lines:
        if "#N/A" in line or "CANCELADO" in line: continue
        # Matches OrderID(64...) then Priority(up to 2 digits) then Items
        parts = re.findall(r"(64\d{4})(\d{1,2})(\d{1,4})", line)
        if parts:
            oid, p_raw, items = parts[0]
            p_int = int(p_raw)
            live_p = get_live_priority(p_int)
            orders.append({"ID": oid, "LiveP": live_p, "Items": int(items), "Name": PRIORITY_NAMES.get(p_int, "Other")})
    # Sort by Live Priority (1 is top), then Items (More is top)
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
    if st.button("CLEAR ALL"): st.rerun()
    st.write("---")
    
    active_ids = []
    pardon_ids = []
    for i in ALL_IDS:
        c1, c2, c3 = st.columns([2,1,1])
        with c1: on = st.toggle(f"ID {i}", value=True, key=f"on_{i}")
        with c2: meal = st.toggle("🍴", key=f"m_{i}")
        with c3: pdr = st.checkbox("OVR", key=f"p_{i}", help="Pardon/New Member")
        
        if on and not meal: active_ids.append(i)
        if pdr: pardon_ids.append(i)

# --- INPUTS ---
col1, col2, col3 = st.columns(3)
with col1: h_in = st.text_area("Historical Data", height=150)
with col2: t_in = st.text_area("Today's Totals", height=150)
with col3: o_in = st.text_area("Pending Orders (Paste here)", height=150)

if st.button("💊 RUN ROTATION"):
    # Parsing Logic
    pat = r"(\d+)[A-Z\s\.]+(\d+)"
    h_blocks = []
    for line in h_in.strip().split('\n'):
        matches = re.findall(pat, line)
        if matches: h_blocks.append({int(k): int(v) for k, v in matches})
    
    t_matches = re.findall(pat, t_in)
    t_counts = {int(k): int(v) for k, v in t_matches if int(k) in active_ids}
    
    pending = parse_pending(o_in)

    # Calculate Rotation Scores
    scores = {}
    temp_sums = [sum(b.values()) for b in h_blocks if b]
    avg_score = sum(temp_sums) / len(temp_sums) if temp_sums else 0
    top_score = 0
    
    for idx in active_ids:
        # 3-day rule
        is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
        h_sum = sum(b.get(idx, 0) for b in h_blocks)
        current = t_counts.get(idx, 0)
        
        if idx in pardon_ids or is_new:
            scores[idx] = int(avg_score / len(ALL_IDS)) + current
        else:
            scores[idx] = h_sum + current
            top_score = max(top_score, scores[idx])
    
    # Penalty for missing IDs not pardoned
    for idx in scores:
        if scores[idx] == 0 and idx not in pardon_ids: scores[idx] = top_score + 5

    # Display Results
    st.write("---")
    st.subheader(f"Current Priority Queue (System Time: {datetime.now().strftime('%H:%M')})")
    
    if not pending:
        st.info("No orders found. Paste data in Column 3.")
    else:
        last_id = None
        for i, order in enumerate(pending[:15]):
            # Get fairest surtidor
            rotation = sorted(scores.items(), key=lambda x: x[1])
            best_id = rotation[0][0]
            if best_id == last_id and len(rotation) > 1:
                best_id = rotation[1][0]
            
            # Update score for the next loop assignment
            scores[best_id] += 1
            last_id = best_id
            
            # Assignment Card
            with st.container():
                # The Checkbox to "clear" it
                col_check, col_card = st.columns([1, 15])
                with col_check:
                    done = st.checkbox("", key=f"d_{order['ID']}_{i}")
                
                if not done:
                    with col_card:
                        st.markdown(f"""
                        <div class="assignment-card">
                            <b style="color:#990000; font-size:20px;">ID {best_id}</b> ⮕ 
                            Order: <b>{order['ID']}</b> | {order['Name']} | {order['Items']} Items
                        </div>
                        """, unsafe_allow_html=True)

st.write("---")
st.caption("Auto-Priority Deadlines: Locals 12:45 | Foráneos 15:00 | Torreón 16:00")
