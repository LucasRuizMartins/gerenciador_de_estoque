import streamlit as st
import pandas as pd
import zipfile
import os
from io import BytesIO
from src import data_loader
from src import global_var
st.title("Processador de Dados Pesados")


# 1. Definir o caminho base
user_profile = os.environ["USERPROFILE"]
path_base = os.path.join(user_profile, 'Carmel Capital', 'Arquivos - Documentos', 
                         '00 - CARMEL ASSET', '01 - OPERACIONAL', 'TECNOLOGIA', 'BASE_ESTOQUE_ANALISE')


if os.path.exists(path_base):
    arquivos_no_diretorio = [f for f in os.listdir(path_base) if os.path.isfile(os.path.join(path_base, f))]
    # Opcional: Filtrar apenas por arquivos ZIP ou CSV
    # arquivos_no_diretorio = [f for f in arquivos_no_diretorio if f.endswith('.zip')]

    if arquivos_no_diretorio:
        # 3. Criar o selectbox
        arquivo_selecionado = st.selectbox('Arquivos disponíveis no servidor:', arquivos_no_diretorio)
        
        # 4. Gerar o caminho completo para passar para sua função de leitura
        file_path = os.path.join(path_base, arquivo_selecionado)
        
        #st.info(f"Caminho pronto: {file_path}")
        
        if st.button("Processar Arquivo Selecionado"):
            data_loader.agregar_chunks(file_path, global_var.COLUNAS_ESTOQUE if global_var.COLUNAS_ESTOQUE else None)
          #  st.success(f"Iniciando leitura de {arquivo_selecionado}...")
    else:
        st.warning("Nenhum arquivo encontrado na pasta especificada.")
else:
    st.error(f"Diretório não encontrado: {path_base}")
    
    
    

# # ─── OPÇÃO 1: Caminho local (recomendado para arquivos grandes) ────────────────



# if file_path and os.path.exists(file_path):
#     # Detecta colunas lendo só o header (sem carregar dados)
#     with zipfile.ZipFile(file_path, 'r') as z:
#         primeiro_csv = [f for f in z.namelist() if f.endswith('.csv')][0]
#         with z.open(primeiro_csv) as f:
#             #colunas_disponiveis = pd.read_csv(f, nrows=0).columns.tolist()
#             colunas_disponiveis =  global_var.COLUNAS_ESTOQUE#pd.read_csv(f, nrows=0, encoding='latin-1',sep=";").columns.tolist()

#     with st.expander("Selecionar colunas"):
#         colunas_sel = st.multiselect(
#             "Colunas", colunas_disponiveis, colunas_disponiveis
#         )

#     if st.button("🚀 Processar"):
#         data_loader.agregar_chunks(file_path, colunas_sel if colunas_sel else None)

# else:
#     if file_path:
#         st.error("file_path não encontrado.")