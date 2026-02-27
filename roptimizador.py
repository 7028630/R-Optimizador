import streamlit as st
import re

# List of IDs currently working
ACTIVE_IDS = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12]

def parse_data(raw_text):
    if not raw_text:
        return {}
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    data = re.findall(pattern, raw_text)
    return {int(id_): int(orders) for id_, orders in data if int(id_) in ACTIVE_IDS}

# --- UI SETUP ---
st.set_page_config(page_title="Optimizer", layout="centered")
st.title("📦 Order Dispatch Optimizer")

# 1. Historical Data Input
with st.expander("📊 Paste Historical/Weekly Data Here"):
    hist_input = st.text_area("Paste previous days/week table here:", height=150)

# 2. Current Data Input
st.subheader("Current Status")
current_input = st.text_area("Paste the CURRENT table here:", height=250)

if current_input:
    # Process Data
    hist_counts = parse_data(hist_input)
    curr_counts = parse_data(current_input)
    
    # Combine counts for total fairness
    total_counts = {}
    for id_ in ACTIVE_IDS:
        total_counts[id_] = hist_counts.get(id_, 0) + curr_counts.get(id_, 0)
    
    # Visual Feedback
    st.success("✅ Information absorbed and processed!")
    
    # Generate Sequence
    st.subheader("Next 20 Turns (Fairness Adjusted):")
    temp_total = total_counts.copy()
    
    results = []
    for i in range(20):
        next_up = min(temp_total, key=temp_total.get)
        results.append(next_up)
        temp_total[next_up] += 1
        
        # Display with bold for the first one
        label = f"**{next_up}**" if i == 0 else f"{next_up}"
        st.markdown(f"* {label}")
else:
    st.info("Waiting for current table data...")
