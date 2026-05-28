import streamlit as st 
import logging
import humanize

# Configuração central de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração central de localização
humanize.activate("pt_BR")

st.set_page_config(
    page_title="Gerenciador de Estoque",
    page_icon="📊",
    layout='wide'
)

st.logo("data/images/LOGO-BRANCO.png")

st.markdown(
    """
    <style>
        /* Aumenta a logo nativa diretamente pelo cabeçalho (quebra as restrições de tamanho) */
        [data-testid="stSidebarHeader"] {
           padding-top: 4rem !important;
           padding-bottom: 4rem !important;
        }
        [data-testid="stSidebarHeader"] img {
            width: 100% !important;
            height: 120px !important;
            max-height: none !important;
            max-width: none !important;
            object-fit: contain !important;
        }
        /* Define o fundo verde apenas para a barra lateral */
        [data-testid="stSidebar"] {
            background-color: #03975eff !important;
        }
        /* Deixa os textos e links da barra lateral brancos para dar contraste */
        [data-testid="stSidebarNav"] span, 
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] label {
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True
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
