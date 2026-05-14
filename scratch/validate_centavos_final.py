import pandas as pd
import numpy as np
import sys
import os
import io

# Add src to path
sys.path.append(os.getcwd())

from src.data_loader import preparar_colunas_valores, ler_csv

# 1. Test the "cents lost" scenario (US CSV)
csv_data = "VALOR\n1234.56\n500.20"
df_csv = ler_csv(io.StringIO(csv_data))
print("CSV US format after reading:")
print(df_csv)

df_csv_p = preparar_colunas_valores(df_csv, ["VALOR"])
print("\nCSV US format after processing:")
print(df_csv_p)
assert df_csv_p.loc[0, "VALOR"] == 1234.56

# 2. Test BR format with currency
df_br = pd.DataFrame({"VALOR": ["R$ 1.234,56", "  R$ 500,20  "]})
df_br_p = preparar_colunas_valores(df_br, ["VALOR"])
print("\nBR format with R$ after processing:")
print(df_br_p)
assert df_br_p.loc[0, "VALOR"] == 1234.56

# 3. Test US format with comma thousands
df_us = pd.DataFrame({"VALOR": ["1,234.56", "500.20"]})
df_us_p = preparar_colunas_valores(df_us, ["VALOR"])
print("\nUS format with comma thousands after processing:")
print(df_us_p)
assert df_us_p.loc[0, "VALOR"] == 1234.56

print("\n✅ All Centavos tests passed!")
