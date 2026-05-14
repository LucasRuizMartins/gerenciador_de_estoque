import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.data_loader import preparar_colunas_valores

# Test cases for values
df_test = pd.DataFrame({
    "VALOR_BR": ["1.234,56", "500,00", "1.000"],
    "VALOR_FLOAT": [1234.56, 500.0, 1000.0],
    "VALOR_MIXED": ["1.234,56", 500.0, np.nan]
})

print("Before processing:")
print(df_test)

df_processed = preparar_colunas_valores(df_test.copy(), ["VALOR_BR", "VALOR_FLOAT", "VALOR_MIXED"])

print("\nAfter NEW processing:")
print(df_processed)
print("\nTypes:")
print(df_processed.dtypes)

# Assertions
assert df_processed.loc[0, "VALOR_FLOAT"] == 1234.56, f"Expected 1234.56, got {df_processed.loc[0, 'VALOR_FLOAT']}"
assert df_processed.loc[0, "VALOR_BR"] == 1234.56
assert df_processed.loc[1, "VALOR_MIXED"] == 500.0
print("\n✅ Values test passed!")
