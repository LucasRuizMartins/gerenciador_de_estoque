import pandas as pd
import streamlit as st
import time

@st.cache_data
def converter_csv(df):
    return df.to_csv(index=False).encode('utf-8')




def limpar_cpf_cnpj(valor: str) -> str:
    """Remove caracteres não numéricos de uma string."""
    if not isinstance(valor, str):
        return str(valor)
    return "".join(filter(str.isdigit, valor))
