import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.data_loader import preparar_colunas_datas

# Test cases for dates
df_test = pd.DataFrame({
    "DATA_BR": ["01/05/2024", "13/05/2024", "31/05/2024"],
    "DATA_ISO": ["2024-05-01", "2024-05-13", "2024-05-31"],
})

print("Before processing:")
print(df_test)

df_p = preparar_colunas_datas(df_test.copy(), ["DATA_BR", "DATA_ISO"])
print("\nAfter NEW processing:")
print(df_p)

# Show months
months_br = df_p["DATA_BR"].dt.to_period("M").tolist()
months_iso = df_p["DATA_ISO"].dt.to_period("M").tolist()

print("\nMonths (to_period('M')):")
print("BR:", months_br)
print("ISO:", months_iso)

# Assertions
assert all(m == pd.Period("2024-05", "M") for m in months_br)
assert all(m == pd.Period("2024-05", "M") for m in months_iso)
print("\n✅ Dates test passed!")
