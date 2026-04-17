import streamlit as st 


st.set_page_config(layout='wide')



pagina_dados = st.Page(
    "pages/pagina_dados.py", 
    title="Dashboard", 
    icon="📊"
)

pagina_dados_processados = st.Page(
    "pages/pagina_dados_processados.py", 
    title="Processamento", 
    icon="📊",
        default=True
)


pg = st.navigation([pagina_dados,pagina_dados_processados])


pg.run()
