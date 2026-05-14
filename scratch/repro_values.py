import pandas as pd
import numpy as np

def preparar_colunas_valores_current(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for col_v in colunas:
        if col_v in df.columns:
            serie = df[col_v]
            if isinstance(serie, pd.DataFrame):
                serie = serie.iloc[:, 0]
            df[col_v] = pd.to_numeric(
                serie.astype(str)
                     .str.replace(".", "", regex=False)
                     .str.replace(",", ".", regex=False),
                errors="coerce"
            )
    return df

# Test cases for values
df_test = pd.DataFrame({
    "VALOR_BR": ["1.234,56", "500,00", "1.000"],
    "VALOR_FLOAT": [1234.56, 500.0, 1000.0],
    "VALOR_MIXED": ["1.234,56", 500.0, np.nan]
})

print("Before processing:")
print(df_test)

df_processed = preparar_colunas_valores_current(df_test.copy(), ["VALOR_BR", "VALOR_FLOAT", "VALOR_MIXED"])

print("\nAfter current processing:")
print(df_processed)
print("\nTypes:")
print(df_processed.dtypes)

# Observe that VALOR_FLOAT became 123456.0 (cents lost)
# Because 1234.56 -> "1234.56" -> "123456" -> 123456.0
