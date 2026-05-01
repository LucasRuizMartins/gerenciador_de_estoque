"""
Página Streamlit: Classificador de Históricos Financeiros.

Permite ao usuário:
  1. Selecionar um modelo treinado da pasta models/
  2. Fazer upload de um arquivo Excel com históricos
  3. Classificar automaticamente cada linha
  4. Baixar o resultado em Excel
"""

import re
import os
import io
import joblib
import pandas as pd
import streamlit as st

import unicodedata
import numpy as np

# CONFIGURAÇÕES
PASTA_MODELOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
COLUNA_RESULTADO = 'Classificacao_Modelo'
CATEGORIA_DESCONHECIDA = 'Cadastrar Nova Categoria'

# Limiar de confiança: abaixo disso o modelo marca como desconhecido.
# Ajuste entre 0.0 (mais permissivo) e 2.0+ (mais restritivo)
LIMIAR_CONFIANCA = 0.6


# FUNÇÕES AUXILIARES

def limpar_texto(texto: str) -> str:
    """Normaliza o texto do histórico para o padrão esperado pelo modelo."""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.lower()
    texto = re.sub(r'\d+', '', texto)       # Remove números
    texto = re.sub(r'[^\w\s]', ' ', texto)  # Remove pontuação
    texto = " ".join(texto.split())          # Remove espaços extras
    return texto


def _normalizar_nome(nome: str) -> str:
    """Remove acentos e coloca em minúsculas para comparação."""
    nfkd = unicodedata.normalize('NFKD', nome)
    sem_acento = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower().strip()


def detectar_coluna_historico(colunas: list[str]) -> str | None:
    """Tenta encontrar automaticamente a coluna de histórico.

    Procura por colunas cujo nome normalizado contenha 'historico'.
    Retorna o nome original da coluna (com acento/maiúsculas) ou None.
    """
    for col in colunas:
        if 'historico' in _normalizar_nome(col):
            return col
    return None


@st.cache_data
def listar_modelos(pasta: str) -> list[str]:
    """Escaneia a pasta models/ e retorna os arquivos .joblib ou .pkl."""
    if not os.path.isdir(pasta):
        return []
    extensoes = ('.joblib', '.pkl')
    arquivos = sorted(
        [f for f in os.listdir(pasta) if f.endswith(extensoes)],
        reverse=True  # Mais recentes primeiro
    )
    return arquivos


@st.cache_resource
def carregar_modelo(caminho: str):
    """Carrega e armazena o modelo em cache para evitar recarregamentos."""
    return joblib.load(caminho)


def classificar_com_limiar(modelo, textos: pd.Series, limiar: float) -> list[dict]:
    """Classifica textos e retorna um dicionário com:
    - categoria_final: a classe final (ou DESCONHECIDA se confiança for baixa)
    - palpite_modelo: o que o modelo previu originalmente
    - score: a pontuação de confiança
    """
    scores = modelo.decision_function(textos)
    if scores.ndim == 1:
        scores = scores.reshape(-1, 1)
    
    max_scores = np.max(scores, axis=1)
    previsoes = modelo.predict(textos)
    
    resultados = []
    for cat, score in zip(previsoes, max_scores):
        cat_final = cat if score >= limiar else CATEGORIA_DESCONHECIDA
        resultados.append({
            'categoria_final': cat_final,
            'palpite_modelo': cat,
            'score': round(float(score), 3)
        })
    return resultados


def converter_para_excel(df: pd.DataFrame) -> bytes:
    """Converte um DataFrame para bytes no formato Excel."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Classificado')
    return buffer.getvalue()


def mesclar_debito_credito(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None, str | None]:
    """Detecta colunas de Débito e Crédito (insensível a acento/maiúsculas),
    torna os valores de Débito negativos e mescla ambas em 'Lançamento (D/C)'.

    Retorna o DataFrame modificado e os nomes originais das colunas encontradas.
    """
    col_debito = None
    col_credito = None

    for col in df.columns:
        nome_norm = _normalizar_nome(col)
        if 'debito' in nome_norm and col_debito is None:
            col_debito = col
        elif 'credito' in nome_norm and col_credito is None:
            col_credito = col

    if col_debito is None and col_credito is None:
        return df, None, None

    # Converte para numérico (NaN onde estiver vazio)
    if col_debito is not None:
        df[col_debito] = pd.to_numeric(df[col_debito], errors='coerce')
    if col_credito is not None:
        df[col_credito] = pd.to_numeric(df[col_credito], errors='coerce')

    # Tratamento Nan e Mesclagem: 
    if col_debito is not None and col_credito is not None:
        df['Lançamento (D/C)'] = df[col_credito].fillna(0) + (-df[col_debito].fillna(0))
        # Zera onde ambos eram NaN (linha sem valor nenhum)
        mask_ambos_nan = df[col_credito].isna() & df[col_debito].isna()
        df.loc[mask_ambos_nan, 'Lançamento (D/C)'] = None
    
    # crédito fica positivo, débito vira negativo
    elif col_credito is not None:
        df['Lançamento (D/C)'] = df[col_credito]
    else:
        df['Lançamento (D/C)'] = -df[col_debito]

    # Remove as colunas originais
    colunas_remover = [c for c in [col_debito, col_credito] if c is not None]
    df = df.drop(columns=colunas_remover)

    return df, col_debito, col_credito


# INTERFACE
st.title("Classificador de Históricos")
st.markdown("Classifique automaticamente os históricos financeiros usando um modelo de Machine Learning treinado.")


# --- Coluna de Configurações e Coluna de Upload ---
col_cfg, col_upload = st.columns([1, 2], gap="large")

with col_cfg:
    st.subheader("⚙️ Configurações")

    # SELEÇÃO DO MODELO
    modelos_disponiveis = listar_modelos(PASTA_MODELOS)

    if not modelos_disponiveis:
        st.error(
            "Nenhum modelo encontrado na pasta `models/`.\n\n"
            "Execute o script `notebooks/criacao_modelos.py` para treinar e salvar um modelo."
        )
        st.stop()

    modelo_selecionado = st.selectbox(
        label="💻 Selecione o modelo",
        options=modelos_disponiveis,
        help="Os modelos são listados do mais recente para o mais antigo."
    )

    caminho_modelo = os.path.join(PASTA_MODELOS, modelo_selecionado)

    with st.spinner("Carregando modelo..."):
        modelo = carregar_modelo(caminho_modelo)

    st.success(f"Modelo carregado: `{modelo_selecionado}`")
    

    # Exibe as categorias que o modelo conhece
    with st.expander("📋 Ver categorias do modelo"):
        categorias = modelo.classes_
        st.write(f"**{len(categorias)} categorias:**")
        for cat in sorted(categorias):
            st.write(f"- {cat}")

    # LIMIAR DE CONFIANÇA
    st.subheader("🎚️ Sensibilidade")
    limiar = st.slider(
        label="Limiar de confiança",
        min_value=0.0,
        max_value=2.0,
        value=LIMIAR_CONFIANCA,
        step=0.05,
        help=(
            "Pontuação mínima para aceitar a classificação do modelo. "
            "Abaixo desse valor, a linha é marcada como 'Cadastrar Nova Categoria'. "
            "Valores menores = mais permissivo. Valores maiores = mais restritivo."
        )
    )

    # Botão de processamento aqui nas configurações
    if st.button("🚀 Iniciar Classificação", use_container_width=True, type="primary"):
        st.session_state['disparar_processo'] = True

with col_upload:
    st.subheader("📂 Upload do Arquivo")

    arquivo_excel = st.file_uploader(
        label="Faça upload do arquivo Excel",
        type=["xlsx"],
        help="O arquivo deve conter uma coluna com os históricos financeiros."
    )

    if arquivo_excel is not None:
        # LEITURA DO ARQUIVO 
        try:
            xls = pd.ExcelFile(arquivo_excel)
            # primeiro lista as abas disponíveis
            abas_disponiveis = xls.sheet_names
        except Exception as e:
            st.error(f"Erro ao abrir o arquivo: {e}")
            st.stop()

        # Seleção da aba
        aba_selecionada = st.selectbox("📄 Selecione a aba do Excel", options=abas_disponiveis)

        # Se a aba mudar, limpamos o resultado anterior para evitar erros de colunas diferentes
        if 'ultima_aba' not in st.session_state or st.session_state['ultima_aba'] != aba_selecionada:
            st.session_state['ultima_aba'] = aba_selecionada
            if 'df_resultado' in st.session_state:
                del st.session_state['df_resultado']
                st.rerun() # Reinicia para limpar a tela

        try:
            df = pd.read_excel(xls, sheet_name=aba_selecionada)
        except Exception as e:
            st.error(f"Erro ao ler a aba '{aba_selecionada}': {e}")
            st.stop()

        # --- VALIDAÇÃO: primeira linha pode ser um título  ---
        # Se algum nome de coluna normalizado contiver "transacoes", significa que a
        # verdadeira linha de cabeçalho está na linha 2 — relemos pulando a linha 1.
        nomes_colunas_norm = [_normalizar_nome(str(c)) for c in df.columns]
        if any('transacoes' in nome for nome in nomes_colunas_norm):
            df = pd.read_excel(xls, sheet_name=aba_selecionada, skiprows=1)
            st.caption("ℹ️ Linha de título 'transacoes' detectada e ignorada automaticamente.")

        # --- DETECÇÃO AUTOMÁTICA DA COLUNA DE HISTÓRICO ---
        coluna_detectada = detectar_coluna_historico(df.columns.tolist())

        if coluna_detectada:
            coluna_historico_input = st.selectbox(
                "🗂️ Coluna de histórico detectada",
                options=df.columns.tolist(),
                index=df.columns.tolist().index(coluna_detectada),
                help="Detectada automaticamente. Você pode trocar se necessário."
            )
            st.caption(f"✅ Coluna detectada automaticamente: `{coluna_detectada}`")
        else:
            coluna_historico_input = st.selectbox(
                "🗂️ Selecione a coluna de histórico",
                options=df.columns.tolist(),
                help="Nenhuma coluna 'historico' foi detectada. Selecione manualmente."
            )
            st.warning("Nenhuma coluna com nome 'historico' foi encontrada.")
        st.info(f"Arquivo carregado: **{arquivo_excel.name}** — {len(df):,} linhas encontradas.")
        if st.session_state.get('disparar_processo', False):
            # 4. PROCESSAMENTO
            with st.spinner("Classificando históricos..."):
                df['_Historico_Limpo'] = df[coluna_historico_input].apply(limpar_texto)
                
                # Chama a função que retorna a lista de dicionários
                resultados = classificar_com_limiar(modelo, df['_Historico_Limpo'], limiar)
                
                # Extrai cada campo para colunas separadas
                df[COLUNA_RESULTADO] = [r['categoria_final'] for r in resultados]
                df['CLASSIFICACAO_MODELO'] = [r['palpite_modelo'] for r in resultados]
                df['CONFIANCA'] = [r['score'] for r in resultados]
                
                df = df.drop(columns=['_Historico_Limpo'])

                # --- MESCLAGEM DÉBITO / CRÉDITO ---
                df, col_deb_encontrada, col_cred_encontrada = mesclar_debito_credito(df)
                
                # Salva o resultado e limpa o gatilho
                st.session_state['df_resultado'] = df
                st.session_state['colunas_mescladas'] = (col_deb_encontrada, col_cred_encontrada)
                st.session_state['disparar_processo'] = False
                st.success("Processamento concluído!")

        # Só exibe os resultados se eles existirem no session_state
        if 'df_resultado' in st.session_state:
            df_proc = st.session_state['df_resultado']
            col_deb_encontrada, col_cred_encontrada = st.session_state['colunas_mescladas']
            
            n_desconhecidos = (df_proc[COLUNA_RESULTADO] == CATEGORIA_DESCONHECIDA).sum()

            # PREVIEW E MÉTRICAS
            st.divider()
            st.subheader("📊 Resultado")

            # Métricas por categoria
            contagem_categorias = df_proc[COLUNA_RESULTADO].value_counts().reset_index()
            contagem_categorias.columns = ['Categoria', 'Quantidade']

            col_result_1, col_result_2, col_result_3 = st.columns(3)

            with col_result_1:
                st.metric("Total de registros", f"{len(df_proc):,}")

            with col_result_2:
                st.metric("Categorias distintas", f"{df_proc[COLUNA_RESULTADO].nunique()}")

            with col_result_3:
                st.metric("Não classificadas", f"{n_desconhecidos}")

            col_m1, col_m2 = st.columns([2, 3])
            
            with col_m1:
                st.dataframe(
                    contagem_categorias,
                    use_container_width=True,
                    hide_index=True
                )

            with col_m2:
                # Usa a coluna de histórico que foi selecionada no início
                try:
                    if coluna_historico_input in df_proc.columns:
                        st.dataframe(
                            df_proc[[coluna_historico_input, COLUNA_RESULTADO]].head(50),
                            use_container_width=True,
                            hide_index=True
                        )
                        if len(df_proc) > 50:
                            st.caption(f"Exibindo 50 de {len(df_proc):,} linhas.")
                    else:
                        st.warning(f"⚠️ Coluna '{coluna_historico_input}' não encontrada no resultado.")
                except Exception:
                    st.error("❌ Histórico não encontrado ou erro ao exibir preview.")

            with st.expander("ℹ️ Detalhes das categorias desconhecidas"):
                linhas_desconhecidas = df_proc[df_proc[COLUNA_RESULTADO] == CATEGORIA_DESCONHECIDA].copy()
                if not linhas_desconhecidas.empty:
                    st.markdown(f"O modelo identificou os seguintes padrões, mas a confiança foi menor que **{limiar:.2f}**:")
                    
                    # Renomeia para exibição amigável na UI
                    linhas_desconhecidas_view = linhas_desconhecidas.rename(columns={
                        'CLASSIFICACAO_MODELO': 'SUGESTÃO_MODELO',
                        'CONFIANCA': 'CONFIANÇA'
                    })

                    resumo_sugestoes = linhas_desconhecidas_view.groupby('SUGESTÃO_MODELO').agg(
                        Quantidade=('SUGESTÃO_MODELO', 'count'),
                        Confianca_Media=('CONFIANÇA', 'mean')
                    ).sort_values(by='Quantidade', ascending=False).reset_index()
                    
                    st.write("**Sugestões de Categorias para Cadastro:**")
                    st.dataframe(
                        resumo_sugestoes.style.format({'Confianca_Media': "{:.1%}"}),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.divider()
                    st.write("**Detalhamento das Linhas:**")
                    display_cols = [coluna_historico_input, 'SUGESTÃO_MODELO', 'CONFIANÇA']
                    st.dataframe(
                        linhas_desconhecidas_view[display_cols].style.format({'CONFIANÇA': "{:.1%}"}),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success("Todas as linhas foram classificadas com confiança suficiente!")

            # DOWNLOAD E INFO DE MESCLAGEM
            if col_deb_encontrada or col_cred_encontrada:
                partes = []
                if col_deb_encontrada: partes.append(f"`{col_deb_encontrada}`")
                if col_cred_encontrada: partes.append(f"`{col_cred_encontrada}`")
                st.info(f"🔄 Colunas mescladas em **Lançamento (D/C)**: {' + '.join(partes)}")

            st.divider()
            # Remove as colunas técnicas antes de gerar o download
            df_download = df_proc.drop(columns=['CLASSIFICACAO_MODELO', 'CONFIANCA'], errors='ignore')
            excel_bytes = converter_para_excel(df_download)
            nome_download = arquivo_excel.name.replace('.xlsx', f'_classificado.xlsx')

            st.download_button(
                label="⬇️ Baixar Excel Classificado",
                data=excel_bytes,
                file_name=nome_download,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

    else:
        st.info("Faça upload de um arquivo `.xlsx` para começar.")
        st.markdown(
            """
            **Formato esperado do arquivo:**
            | Historico | ... outras colunas ... |
            |---|---|
            | PAGAMENTO FORNECEDOR XYZ | ... |
            | RECEBIMENTO CLIENTE ABC | ... |
            """
        )
