from zipfile import ZipFile 
import streamlit as st
import pandas as pd
import zipfile


def read_zipfile_from_buffer(uploaded_zip):
    dfs = []

    with ZipFile(uploaded_zip) as z:
        for filename in z.namelist():
            if filename.endswith('.csv'):
                with z.open(filename) as f:
                    df = pd.read_csv(f, 
                                    encoding='ISO-8859-1',
                                    on_bad_lines='skip', 
                                    delimiter=';',
                                    decimal=',', 
                                    thousands='.',  
                                    low_memory=False)
                    dfs.append(df)
    return dfs
                    
                    
CHUNK_SIZE = 100_000  # linhas por chunk

def processar_zip_por_chunks(caminho_zip: str, colunas: list = None):
    """
    Lê cada CSV dentro do ZIP em chunks, evitando carregar tudo na RAM.
    Retorna um generator de DataFrames.
    """
    with zipfile.ZipFile(caminho_zip, 'r') as z:
        csvs = [f for f in z.namelist() if f.endswith('.csv')]
        #st.info(f"Encontrados {len(csvs)} CSVs no ZIP")

        for nome_csv in csvs:
            with z.open(nome_csv) as arquivo:
                # Lê em chunks — nunca carrega o CSV inteiro
                for chunk in pd.read_csv(
                    arquivo,
                    chunksize=CHUNK_SIZE,
                    encoding='ISO-8859-1',
                    sep=";",
                    usecols=colunas,       # só as colunas necessárias
                    low_memory=False
                ):
                    yield chunk


def agregar_chunks(caminho_zip: str, colunas: list = None):
    """
    Exemplo de agregação sem guardar tudo na RAM.
    Adapte a lógica de negócio aqui.
    """
    total_linhas = 0
    resultado_parcial = []

    progress = st.progress(0, text="Processando...")
    
    chunks = list(processar_zip_por_chunks(caminho_zip, colunas))
    total_chunks = len(chunks)

    for i, chunk in enumerate(processar_zip_por_chunks(caminho_zip, colunas)):
        total_linhas += len(chunk)

        # ⚠️ Faça sua agregação AQUI — não acumule os chunks crus!
        # Exemplo: somar por grupo
        # parcial = chunk.groupby('coluna_chave')['valor'].sum()
        # resultado_parcial.append(parcial)

        progress.progress((i + 1) / max(total_chunks, 1), 
                         text=f"Processando chunk {i+1} — {total_linhas:,} linhas")

    st.success(f"✅ Total processado: {total_linhas:,} linhas")
    
    # Se precisar combinar agregações parciais:
    # return pd.concat(resultado_parcial).groupby(level=0).sum()


def ler_zip(file):
    dfs = []
    with ZipFile(file) as z:
        for name in z.namelist():
            if name.endswith(".csv"):
                with z.open(name) as f:
                    dfs.append(pd.read_csv(
                        f,
                        encoding="ISO-8859-1",
                        delimiter=";",
                        decimal=",",
                        thousands=".",
                        on_bad_lines="skip",
                        low_memory=False
                    ))
    return pd.concat(dfs, ignore_index=True)

def ler_csv(file):
    return pd.read_csv(
        file,
        encoding="ISO-8859-1",
        delimiter=";",
        decimal=",",
        thousands=".",
        on_bad_lines="skip",
        low_memory=False
    )

