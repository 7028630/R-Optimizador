import streamlit as st
import re

# --- CONFIGURATION ---
# List of IDs currently working today
ACTIVE_IDS = [1, 2, 3, 5, 6, 8, 9, 10, 11, 12]
TARGET = 55

def get_next_sequence(raw_text, num_turns=20):
    # Regex to extract ID and Current Orders from your copy-paste format
    pattern = r"(\d+)[A-Z\s\.]+(\d+)"
    data = re.findall(pattern, raw_text)
    
    # Create dictionary of {ID: Orders}
    counts = {int(id_): int(orders) for id_, orders in data if int(id_) in ACTIVE_IDS}
    
    # Logic: Fill the gap for those furthest from the 55 target
    sequence = []
    temp_counts = counts.copy()
    
    for _ in range(num_turns):
        # Pick the person with the lowest current order count
        next_up = min(temp_counts, key=temp_counts.get)
        sequence.append(next_up)
        temp_counts[next_up] += 1
        
    return sequence

# --- STREAMLIT UI ---
st.title("📦 Order Dispatch Optimizer")
st.write("Paste the current table below to get the next 20 turns.")

# Input area for the copy-paste
input_data = st.text_area("Paste table here:", height=300)

if input_data:
    try:
        results = get_next_sequence(input_data)
        st.subheader("Next 20 Turns:")
        for i, picker_id in enumerate(results):
            # Bold the first one as requested
            if i == 0:
                st.markdown(f"* **{picker_id}**")
            else:
                st.markdown(f"* {picker_id}")
    except Exception as e:
        st.error("Make sure the table format is correct!")

st.info("Coming Soon: Priority Type & Timeframe filters.")
