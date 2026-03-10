import re
import pandas as pd

def parse_surtidor_data(raw_text):
    """
    Unified parser for structured and collapsed "Surtidor" data.
    Works even if the data is squashed together.
    """
    # Pattern Logic:
    # (\d+)            -> Group 1: The ID (1-2 digits)
    # ([A-Z\.\s/]+)    -> Group 2: The Name (Letters, dots, spaces, slashes)
    # (\d+)            -> Group 3: Pedidos (The first number after the name)
    # ([\d\.\-]+)      -> Group 4: Piezas (Numbers with decimals or a dash)
    pattern = r'(\d{1,2})([A-Z\.\s/]{3,25}?)(\d+)([\d\.\-]+)'
    
    # Pre-cleaning: Remove headers and footer noise to prevent false matches
    clean_text = re.sub(r'No\.|SURTIDOR|PEDIDOS|PIEZAS|Total.*|SIN NOMBRE', '', raw_text, flags=re.IGNORECASE)
    
    matches = re.findall(pattern, clean_text)
    
    data = []
    for m in matches:
        idx, name, pedidos, piezas = m
        
        # Clean up the name from trailing/leading whitespace
        name = name.strip()
        
        # Convert piezas: replace dash with 0, remove extra dots if it's a thousands separator
        piezas_clean = piezas.replace('-', '0').strip()
        
        data.append({
            "No.": int(idx),
            "Surtidor": name,
            "Pedidos": int(pedidos),
            "Piezas": piezas_clean
        })

    df = pd.DataFrame(data)
    
    # If the same ID appears multiple times (History + Today), we group them
    if not df.empty:
        summary = df.groupby(['No.', 'Surtidor']).agg({
            'Pedidos': 'sum',
            'Piezas': lambda x: "Combined Records" # Or sum if you convert to float
        }).reset_index()
        return df, summary
    
    return df, None

# --- HOW TO USE ---
# Replace the triple quotes content with your actual paste
raw_input = """
[PASTE YOUR ENTIRE HISTORIAL AND TODAY'S DATA HERE]
"""

all_records, total_summary = parse_surtidor_data(raw_input)

# Output results
print("--- DETAILED RECORDS EXTRACTED ---")
print(all_records.to_string(index=False))

# Optional: Export to CSV for Excel
# all_records.to_csv("surtidor_report.csv", index=False)
