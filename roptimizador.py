if st.button("💊 PROCESAR TURNOS"):
    parsed = parse_pending(o_in)
    if not parsed: 
        st.error("Sin pedidos.")
    else:
        st.session_state.pedidos = parsed
        # This regex now specifically handles IDs followed by Names and then the Total
        pat = r"(\d+)\s+[A-Z\s\.\-_]+\s+(\d+)"
        
        h_blocks = []
        if h_in.strip():
            # Split by double newline or "Total" to separate the historical lists you provided
            raw_blocks = re.split(r'Total\s+\d+|No\.', h_in)
            for block in raw_blocks:
                m = re.findall(pat, block)
                if m:
                    h_blocks.append({int(k): int(v) for k, v in m})
        
        # Parse Totales (current workload)
        t_counts = {int(k): int(v) for k, v in re.findall(pat, t_in) if int(k) in active_ids}
        
        scores = {}
        # Calculate baseline to avoid overloading new/returning people
        temp_sums = [sum(b.values()) for b in h_blocks if b]
        avg_per_block = sum(temp_sums) / len(temp_sums) if temp_sums else 0
        baseline = int(avg_per_block / len(ALL_IDS)) if avg_per_block > 0 else 0
        
        max_seen = 0
        for idx in active_ids:
            # 1. Historical Load
            h_sum = sum(b.get(idx, 0) for b in h_blocks)
            
            # 2. Activity Check (Last 2 blocks)
            # If they haven't appeared recently, we don't treat them as 0 (to avoid flooding)
            is_recent = any(b.get(idx, 0) > 0 for b in h_blocks[-2:]) if len(h_blocks) >= 2 else True
            
            # 3. Final Score Calculation
            current_t = t_counts.get(idx, 0)
            
            if idx in pardon_ids or not is_recent:
                scores[idx] = baseline + current_t
            else:
                scores[idx] = h_sum + current_t
                
            if scores[idx] > max_seen:
                max_seen = scores[idx]

        # Ensure those with absolute 0 are placed behind the busiest person + a small buffer
        for idx in scores:
            if scores[idx] == 0 and idx not in pardon_ids:
                scores[idx] = max_seen + 5

        st.session_state.scores = scores
        st.rerun()
