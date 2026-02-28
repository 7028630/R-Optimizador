import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & PRIORITY MAP ---
ALL_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]

# Priority Mapping
PRIORITY_MAP = {
    1: "Local Urgente (1)", 2: "Local Urgente (2)",
    3: "Apodaca", 4: "Guadalupe", 5: "Santa Catarina",
    6: "Solidaridad", 7: "Unidad", 8: "Sur Foráneo", 9: "Sur",
    10: "Foráneo Urgente", 11: "Foráneo", 12: "Torreón",
    14: "Saltillo", 16: "Local Después de Corte",
    17: "Foráneo Urg. Desp. Corte", 18: "Foráneo Desp. Corte", 19: "Torreón Desp. Corte"
}

def get_dynamic_priority(p_val, current_time):
    # Logic: After 12:45, Locals (3-9) move to 16
    if 3 <= p_val <= 9:
        if current_time >= "12:45": return 16
        return 3 # Grouped importance
    # After 15:00, Foráneos (10-11) move to 18
    if p_val in [10, 11] and current_time >= "15:00":
        return 18
    # After 16:00, Torreón (12) moves to 19
    if p_val == 12 and current_time >= "16:00":
        return 19
    return p_val

def parse_pending_orders_complex(raw_text):
    if not raw_text: return []
    now_str = datetime.now().strftime("%H:%M")
    lines = raw_text.strip().split('\n')
    orders = []
    for line in lines:
        if "#N/A" in line or "CANCELADO" in line: continue
        parts = re.findall(r"(64\d{4})(\d{1,2})(\d{1,4})", line)
        if parts:
            order_id, p_raw, items = parts[0]
            p_val = int(p_raw)
            # Apply time-based logic
            final_p = get_dynamic_priority(p_val, now_str)
            orders.append({"ID": order_id, "P": final_p, "Items": int(items), "RawP": p_val})
    return sorted(orders, key=lambda x: (x['P'], -x['Items']))

# --- UI SETUP ---
st.set_page_config(page_title="Warehouse Ops", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F4F4F4; }
    .assignment-card { background: white; padding: 10px; border-left: 10px solid #990000; border-radius: 4px; margin-bottom: 5px; }
    .done { opacity: 0.4; text-decoration: line-through; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SIMPLE PERSONNEL & MEALS ---
with st.sidebar:
    st.header("Team Status")
    if st.button("RESET ALL DATA"): st.rerun()
    
    st.write("---")
    st.subheader("Shift / Meal Toggle")
    # Simple checkbox list is much more stable than the data_editor for mobile/fast use
    active_ids = []
    for i in ALL_IDS:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            is_active = st.toggle(f"ID {i} Working", value=True, key=f"active_{i}")
        with col_b:
            is_meal = st.toggle("🍴", value=False, key=f"meal_{i}")
        
        if is_active and not is_meal:
            active_ids.append(i)
    
    st.write("---")
    overrides = [id_n for id_n in ALL_IDS if st.checkbox(f"Pardon ID {id_n}", key=f"ovr_{id_n}")]

# --- MAIN CONTENT ---
c1, c2, c3 = st.columns(3)
with c1: hist_in = st.text_area("Historical Totals", height=150)
with c2: today_in = st.text_area("Today's Totals", height=150)
with c3: orders_in = st.text_area("Google Sheet Dump", height=150)

if st.button("💊 CALCULATE ASSIGNMENTS"):
    # Logic: 3-day absence & Historical parsing
    # (Regex from previous step kept for stability)
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    hist_blocks = []
    for b in hist_in.strip().split('\n'):
        d = re.findall(pattern, b)
        if d: hist_blocks.append({int(k): int(v) for k, v in d})
    
    curr_data = re.findall(pattern, today_in)
    curr_counts = {int(k): int(v) for k, v in curr_data if int(k) in active_ids}
    
    # Priority Sorting
    pending = parse_pending_orders_complex(orders_in)

    # Rotation Logic
    scores = {}
    temp_sums = [sum(b.values()) for b in hist_blocks if b]
    avg = sum(temp_sums) / len(temp_sums) if temp_sums else 0
    max_s = 0
    
    for idx in active_ids:
        absent = len(hist_blocks) >= 3 and sum([b.get(idx, 0) for b in hist_blocks[-3:]]) == 0
        h_total = sum(b.get(idx, 0) for b in hist_blocks)
        c_val = curr_counts.get(idx, 0)
        
        if idx in overrides or absent:
            scores[idx] = int(avg / len(ALL_IDS)) + c_val
        else:
            scores[idx] = h_total + c_val
            max_s = max(max_s, scores[idx])
    
    for idx in scores:
        if scores[idx] == 0 and idx not in overrides: scores[idx] = max_s + 5

    # --- DISPLAY QUEUE WITH "CHECK-OFF" ---
    st.subheader(f"🚀 Live Queue (Current Time: {datetime.now().strftime('%H:%M')})")
    
    if not pending:
        st.info("No orders found. Ensure you pasted the columns correctly.")
    else:
        last_id = None
        for i, order in enumerate(pending[:20]):
            # Get next person in rotation
            sorted_scores = sorted(scores.items(), key=lambda x: x[1])
            best_id = sorted_scores[0][0]
            if best_id == last_id and len(sorted_scores) > 1:
                best_id = sorted_scores[1][0]
            
            # Update score for the next loop iteration
            scores[best_id] += 1
            last_id = best_id
            
            # Assignment Box with a "Done" checkbox
            with st.container():
                is_done = st.checkbox(f"Mark Assigned: {order['ID']}", key=f"check_{order['ID']}_{i}")
                card_class = "assignment-card done" if is_done else "assignment-card"
                
                if not is_done: # Only show details if not checked off (per your request)
                    st.markdown(f"""
                    <div class="{card_class}">
                        <b style="color:#990000; font-size:18px;">ID {best_id}</b> ⮕ 
                        Order: <b>{order['ID']}</b> | Priority: {PRIORITY_MAP.get(order['RawP'], order['RawP'])} | Items: {order['Items']}
                    </div>
                    """, unsafe_allow_html=
