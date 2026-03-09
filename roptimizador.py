if st.button("💊 PROCESAR TURNOS"):
    parsed = parse_pending(o_in)
    if not parsed: 
        st.error("Sin pedidos.")
    else:
        st.session_state.pedidos = parsed
        # Pattern to capture ID, Name (ignored), and the Count/Total
        pat = r"(\d+)[A-Z\s\.\-_]+(\d+)"
        
        h_blocks = []
        for line in h_in.strip().split('\n'):
            m = re.findall(pat, line)
            if m: h_blocks.append({int(k): int(v) for k, v in m})
        
        # Parse current totals (current workload/session totals)
        t_counts = {int(k): int(v) for k, v in re.findall(pat, t_in) if int(k) in active_ids}
        
        scores = {}
        # Calculate a baseline based on the average performance to handle new/excused IDs
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        total_historical_avg = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        baseline = int(total_historical_avg / len(ALL_IDS)) if total_historical_avg > 0 else 0
        
        top_score = 0
        for idx in active_ids:
            # 1. Calculate Historical Weight (Sum of all provided historical blocks)
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            
            # 2. Check if the user is "New" (No activity in the last 3 blocks)
            is_new = len(h_blocks) >= 3 and sum([b.get(idx, 0) for b in h_blocks[-3:]]) == 0
            
            # 3. Assign Score: 
            # If ID is excused (pardon) or is a new entry, give them the average baseline
            # Otherwise, use their true historical total + their current totals
            current_total = t_counts.get(idx, 0)
            
            if idx in pardon_ids or (is_new and h_sum > 0):
                scores[idx] = baseline + current_total
            else:
                scores[idx] = h_sum + current_total
            
            if scores[idx] > top_score:
                top_score = scores[idx]

        # Penalty for IDs with 0 history to ensure they aren't flooded immediately 
        # unless they are explicitly marked in pardon_ids
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids:
                scores[idx] = top_score + 1

        st.session_state.scores = scores
        st.rerun()
