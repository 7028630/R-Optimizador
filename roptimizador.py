import re
import pandas as pd

def parse_surtidor_data(raw_text):
    # 1. Pattern for 'collapsed' text (Today's data style)
    # Finds: [ID] [Name/Support] [Orders] [Pieces/Dashes]
    collapsed_pattern = r'(\d+)([A-Z\.\s]+(?:[A-Z]+)*)(\d+)([\d\.\-]+)'
    
    # 2. Pattern for 'structured' text (Historical style)
    structured_pattern = r'(\d+)\t+([A-Z\.\s]+)\t+(\d+)\t+([\d\.\-]+)'

    results = []
    
    # Clean the text: Remove "Total" lines and headers to avoid noise
    clean_text = re.sub(r'No\.|SURTIDOR|PEDIDOS|PIEZAS|Total.*', '', raw_text)

    # Try matching structured first, then collapsed
    for line in clean_text.split('\n'):
        line = line.strip()
        if not line: continue
        
        # Check structured (tabs)
        match = re.search(structured_pattern, line)
        if not match:
            # Check collapsed (no spaces)
            match = re.search(collapsed_pattern, line)
            
        if match:
            results.append({
                "ID": match.group(1),
                "Surtidor": match.group(2).strip(),
                "Pedidos": int(match.group(3)),
                "Piezas": match.group(4).replace('-', '0').replace(' ', '')
            })

    return pd.DataFrame(results)

# DATA INPUT
raw_input = """[PASTE EVERYTHING HERE]"""

df = parse_surtidor_data(raw_input)
print(df.to_string(index=False))
