import streamlit as st
import re

# List of all possible IDs
ALL_IDS = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12]

def parse_data(raw_text, active_ids):
    if not raw_text:
        return {}
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    data = re.findall(pattern, raw_text)
    # Only pull data for IDs that are currently "Active" (checked)
    return {int(id_): int(orders) for id_, orders in data if int(id_) in active_ids}

# --- UI SETUP ---
st.set_page_config(page_title="Optimizer", layout="wide")
st.title("📦 Order Dispatch Optimizer")

# Sidebar for "Starting Over" and "Lunch Breaks"
with st.sidebar:
    st.header("Settings")
    if st.button("🔄 Reset / Start Over"):
        st.rerun()
    
    st.write("---")
    st.write("**Who is active right now?**")
    st.info("Uncheck those at lunch or gone for the day.")
    active_selection = []
    for id_num in ALL_IDS:
        if st.checkbox(f"ID {id_num}", value=True):
            active_selection.append(id_num)

# Main Area
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Historical Data")
    hist_input = st.text_area("Paste all previous table(s) here:", height=300)

with col2:
    st.subheader("2. Current Status")
    current_input = st.text_area("Paste the LATEST table here:", height=300)

if current_input:
    hist_counts = parse_data(hist_input, active_selection)
    curr_counts = parse_data(current_input, active_selection)
    
    # Combine counts
    total_counts = {}
    for id_ in active_selection:
        total_counts[id_] = hist_counts.get(id_, 0) + curr_counts.get(id_, 0)
    
    st.success("✅ Processed! Turns adjusted for fairness and active staff.")
    
    # Generate Sequence
    st.subheader("Next 20 Turns:")
    temp_total = total_counts.copy()
    
    # Simple display logic
    cols = st.columns(5)
    for i in range(20):
        next_up = min(temp_total, key=temp_total.get)
        temp_total[next_up] += 1
        
        with cols[i % 5]:
            if i == 0:
                st.markdown(f"### **{next_up}**") # Make the very next turn huge
            else:
                st.write(f"Turn {i+1}: **{next_up}**")
else:
    st.info("Please paste the current table to see the next turns.")
