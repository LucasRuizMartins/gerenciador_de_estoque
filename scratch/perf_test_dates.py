import pandas as pd
import numpy as np
import time

def optimized_dates(serie):
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie).dt.tz_localize(None)
    
    s = serie.astype(str).str.strip()
    is_iso = s.str.contains(r"^\d{4}-\d{2}-\d{2}", regex=True, na=False)
    
    res = pd.Series(pd.NaT, index=serie.index)
    
    # ISO
    if is_iso.any():
        res[is_iso] = pd.to_datetime(s[is_iso], dayfirst=False, errors="coerce")
    
    # BR
    not_iso = ~is_iso
    if not_iso.any():
        res[not_iso] = pd.to_datetime(s[not_iso], dayfirst=True, errors="coerce")
        
    return res

n = 100_000
dates = ["2024-05-01", "01/05/2024"] * (n // 2)
s = pd.Series(dates)

start = time.time()
res = optimized_dates(s)
print(f"Optimized dates (vectorized split): {time.time() - start:.4f}s")
print(res.head())
print("Check:", (res.dt.month == 5).all())
