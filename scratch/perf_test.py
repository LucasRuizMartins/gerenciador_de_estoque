import pandas as pd
import numpy as np
import time

def slow_val(x):
    if pd.isna(x): return x
    s = str(x).strip()
    if "," in s:
        return s.replace(".", "").replace(",", ".")
    return s

def fast_val(serie):
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors="coerce")
    s = serie.astype(str).str.strip()
    has_comma = s.str.contains(",", na=False)
    # vectorized replace
    res = s.copy()
    res[has_comma] = s[has_comma].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(res, errors="coerce")

# Generate 100k rows
n = 100_000
df = pd.DataFrame({
    "VALOR": ["1.234,56"] * n
})

start = time.time()
res_slow = pd.to_numeric(df["VALOR"].apply(slow_val), errors="coerce")
print(f"Slow (apply): {time.time() - start:.4f}s")

start = time.time()
res_fast = fast_val(df["VALOR"])
print(f"Fast (vectorized): {time.time() - start:.4f}s")

# Test dates
dates = ["2024-05-01", "01/05/2024"] * (n // 2)
df_d = pd.DataFrame({"DATA": dates})

start = time.time()
res_mixed = pd.to_datetime(df_d["DATA"], dayfirst=True, format='mixed', errors="coerce")
print(f"Mixed dates (dayfirst=True, format='mixed'): {time.time() - start:.4f}s")
print("First few dates (should both be May 1st):")
print(res_mixed.head())
