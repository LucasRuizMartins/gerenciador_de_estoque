import requests
import pandas as pd
import streamlit as st

URL = 'https://labdados.com/produtos'

@st.cache_data
def get_base(query):
    response = requests.get(URL,params=query)
    dados = pd.DataFrame.from_dict(response.json())
    dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'],format='%d/%m/%Y')
    return dados