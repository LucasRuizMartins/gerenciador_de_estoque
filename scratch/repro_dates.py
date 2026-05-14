import pandas as pd

def preparar_colunas_datas_current(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for col_dt in colunas:
        if col_dt in df.columns:
            serie = df[col_dt]
            df[col_dt] = pd.to_datetime(serie, dayfirst=True, errors="coerce")
    return df

# Test cases for dates
df_test = pd.DataFrame({
    "DATA_BR": ["01/05/2024", "13/05/2024", "31/05/2024"],
    "DATA_ISO": ["2024-05-01", "2024-05-13", "2024-05-31"],
    "DATA_US": ["05/01/2024", "05/13/2024", "05/31/2024"],
})

print("Current processing (dayfirst=True):")
df_p = preparar_colunas_datas_current(df_test.copy(), ["DATA_BR", "DATA_ISO", "DATA_US"])
print(df_p)

# Show months
print("\nMonths (to_period('M')):")
print("BR:", df_p["DATA_BR"].dt.to_period("M").tolist())
print("ISO:", df_p["DATA_ISO"].dt.to_period("M").tolist())
print("US:", df_p["DATA_US"].dt.to_period("M").tolist())
