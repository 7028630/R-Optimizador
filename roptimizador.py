import streamlit as st
import re
import pandas as pd
from datetime import datetime

# --- CONFIGURATION & PRIORITY MAP ---
ALL_IDS = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12]

# Full Priority List provided by user
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

    # Saltillo (14), Sur Foráneo (8), and Top Locals (1,2) NEVER change
    if p_val in [14, 8, 1, 2]:
        return p_val
    
    # 12:45 Deadline: Locals (3-7, 9) -> 16
    if (3 <= p_val <= 7 or p_val == 9) and now >= d1245:
        return 16
    
    # 15:00 Deadline: Foráneos (10-11) -> 18
    if (p_val == 10 or p_val == 11) and now >= d1500:
        return 18
        
    # 16:00 Deadline: Torreón (12) -> 19
    if p_val == 12 and now >= d1600:
        return 19
        
    # Grouping 3-9 for same importance level before deadlines
    if 3 <= p_val <= 9:
        return 3
        
    return p_val

def parse_pending(raw_text):
    if not raw_text: return []
    # Step 1: Force split stuck lines by the "64" Order ID prefix
    raw_text = raw_text.replace("64", "\n64")
    lines = raw_text.strip().split('\n')
    orders = []
    
    for line in lines:
        line = line.strip()
        if "#N/A" in line or "CANCELADO" in line or not line: continue
        
        # Regex explanation:
        # (64\d{4}) -> The 6 digit Order ID
        # (\d{1,2}) -> The next 1 or 2 digits (Priority)
        # (\d+)     -> The remaining digits (Items)
        match = re.search(r"(64\d{4})(\d{1,2})(\d+)", line)
        if match:
            oid, p_raw, items = match.groups()
            p_int = int(p_raw)
            
            # Validation: If the 2-digit priority isn't in our list, 
            # try treating it as a 1-digit priority and shifting the extra digit to Items
            if p_int not in PRIORITY_NAMES and len(p_raw) == 2:
                p_int = int(p_raw[0])
                items = p_raw[1] + items
            
            # Final check to ensure priority is valid
            if p_int in PRIORITY_NAMES:
                live_p = get_live_priority(p_int)
                orders.append({
                    "ID": oid, 
                    "LiveP": live_p, 
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
    if st.button("🔄 CLEAR ALL SESSION DATA"): 
        st.cache_data.clear()
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
with col1: h_in = st.text_area("1. Historical Data", height=150, placeholder="Paste historical tables...")
with col2: t_in = st.text_area("2. Today's Totals", height=150, placeholder="Paste today's surtidor table...")
with col3: o_in = st.text_area("3. Pending Orders", height=150, placeholder="Paste Google Sheet content...")

if st.button("💊 GENERATE ROTATION"):
    if not o_in:
        st.error("Please paste the orders in Column 3.")
    else:
        # Personnel Logic
        pat = r"(\d+)[A-Z\s\.]+(\d+)"
        h_blocks = []
        for line in h_in.strip().split('\n'):
            matches = re.findall(pat, line)
            if matches: h_blocks.append({int(k): int(v) for k, v in matches})
        
        t_matches = re.findall(pat, t_in)
        t_counts = {int(k): int(v) for k, v in t_matches if int(k) in active_ids}
        
        # Order Logic
        pending = parse_pending(o_in)

        # Fairness Math
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

        # Results
        st.write("---")
        st.subheader(f"Next Assignments ({datetime.now().strftime('%H:%M')})")
        
        if not pending:
            st.warning("No orders detected. Check your paste data.")
            with st.expander("Debug: Show Raw Data Split"):
                st.code(o_in.replace("64", "\n64"))
        else:
            last_id = None
            for i, order in enumerate(pending[:25]):
                rotation = sorted(scores.items(), key=lambda x: x[1])
                if not rotation: break
                best_id = rotation[0][0]
                if best_id == last_id and len(rotation) > 1:
                    best_id = rotation[1][0]
                
                scores[best_id] += 1
                last_id = best_id
                
                with st.container():
                    c_check, c_card = st.columns([1, 20])
                    with c_check:
                        done = st.checkbox("", key=f"d_{order['ID']}_{i}")
                    if not done:
                        with c_card:
                            st.markdown(f"""
                            <div class="assignment-card">
                                <b style="color:#990000; font-size:18px;">ID {best_id}</b> ⮕ 
                                <b>{order['ID']}</b> | {order['Name']} | {order['Items']} Items
                            </div>
                            """, unsafe_allow_html=True)

st.write("---")
st.caption("Auto-Priority: Locales 3-9 (Corte @ 12:45) | Foráneos 10-11 (Corte @ 15:00) | Torreón (Corte @ 16:00)")
