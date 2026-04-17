import pandas as pd
import streamlit as st
import time
def formata_numero(valor,prefixo = ''):
    for unidade in ['','mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'



@st.cache_data
def converter_csv(df):
    return df.to_csv(index=False).encode('utf-8')


def mensagem_sucesso():
    sucesso = st.success('arquivo baixado com sucesso', icon = '✅')
    time.sleep(5)
    sucesso.empty()
