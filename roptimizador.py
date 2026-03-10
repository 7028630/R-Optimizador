import re
import pandas as pd

def universal_cleaner(raw_text):
    # 1. First, we remove "Total", "SIN NOMBRE", and "ID" junk that causes 0.0000 results
    text = re.sub(r'SIN NOMBRE|ID \d+|0\.0000|No\.|SURTIDOR|PEDIDOS|PIEZAS|Total', '', raw_text, flags=re.IGNORECASE)
    
    # 2. This regex is the "magic" for squashed data:
    # (\d+)         -> The ID number
    # ([A-Z\.\s]+?) -> The name (stops as soon as it sees the next number)
    # (\d+)         -> The Pedidos
    # ([\d\.\-]+)   -> The Piezas
    pattern = r'(\d+)\s*([A-Za-z\.\s/]+?)\s*(\d+)\s*([\d\.\-]+)'
    
    matches = re.findall(pattern, text)
    
    # 3. If it's STILL blank, try the "Zero-Space" pattern for the 'Today's' data mess
    if not matches:
        # This one looks for numbers directly hitting letters: e.g., 5H.CRUZ252.420
        pattern_collapsed = r'(\d+)([A-Z\.\s/]+)(\d+)([\d\.\-]+)'
        matches = re.findall(pattern_collapsed, text)

    results = []
    for m in matches:
        idx, name, pedidos, piezas = m
        # Only keep it if it's actual work (pedidos > 0)
        if int(pedidos) > 0:
            results.append({
                "No": idx.strip(),
                "Surtidor": name.strip(),
                "Pedidos": int(pedidos),
                "Piezas": piezas.strip()
            })

    return pd.DataFrame(results)

# --- PASTE EVERYTHING BELOW ---
data_blob = """
[PASTE YOUR ENTIRE TEXT HERE]
"""

df = universal_cleaner(data_blob)

if df.empty:
    print("⚠️ Still Blank. Please check if the 'data_blob' variable actually contains the text.")
else:
    print("✅ DATA RECOVERED:")
    print(df.to_string(index=False))
