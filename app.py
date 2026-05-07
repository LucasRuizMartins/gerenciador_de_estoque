import streamlit as st 


st.set_page_config(
    page_title="Gerenciador de Estoque",
    page_icon="📊",
    layout='wide'
)



pagina_estoque = st.Page(
    "pages/pagina_estoque.py", 
    title="Processamento Estoque", 
    icon="📊",
        default=True
)



pagina_liquidacoes = st.Page(
    "pages/pagina_liquidacoes.py",
    title="Análise de Liquidações",
    icon="💰"
)

pagina_aquisicao = st.Page(
    "pages/pagina_aquisicao.py",
    title="Análise de Aquisições",
    icon="📥"
)

pagina_leitor_cnab = st.Page(
    "pages/validador_cnab.py", 
    title="Validador de cnab", 
    icon="📄"
)

pagina_pdd = st.Page(
    "pages/calcular_pdd.py", 
    title="calcular pdd", 
    icon="📉"
)

pagina_classificador = st.Page(
    "pages/classificar_historico.py",
    title="Classificador de Históricos",
    icon="💻"
)

pagina_gerador_remessa = st.Page(
    "pages/gerador_remessa.py",
    title="Gerador de Remessa",
    icon="📄"
)

pg = st.navigation([pagina_estoque, pagina_liquidacoes, pagina_aquisicao, pagina_pdd, pagina_classificador, pagina_leitor_cnab, pagina_gerador_remessa])


pg.run()
