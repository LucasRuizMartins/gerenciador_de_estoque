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


ModuleNotFoundError: No module named 'classes'
Traceback:
File "C:\Users\deth_\Carmel Capital\TECNOLOGIA - Geral\DESENVOLVIMENTO\PYTHON\PROJETOS_EM_DESENVOLVIMENTO\gerenciador_de_estoque\venv\Lib\site-packages\streamlit\runtime\scriptrunner\exec_code.py", line 129, in exec_func_with_error_handling
    result = func()
File "C:\Users\deth_\Carmel Capital\TECNOLOGIA - Geral\DESENVOLVIMENTO\PYTHON\PROJETOS_EM_DESENVOLVIMENTO\gerenciador_de_estoque\venv\Lib\site-packages\streamlit\runtime\scriptrunner\script_runner.py", line 689, in code_to_exec
    exec(code, module.__dict__)  # noqa: S102
    ~~~~^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\deth_\Carmel Capital\TECNOLOGIA - Geral\DESENVOLVIMENTO\PYTHON\PROJETOS_EM_DESENVOLVIMENTO\gerenciador_de_estoque\app.py", line 32, in <module>
    pg.run()
    ~~~~~~^^
File "C:\Users\deth_\Carmel Capital\TECNOLOGIA - Geral\DESENVOLVIMENTO\PYTHON\PROJETOS_EM_DESENVOLVIMENTO\gerenciador_de_estoque\venv\Lib\site-packages\streamlit\navigation\page.py", line 490, in run
    exec(code, module.__dict__)  # noqa: S102
    ~~~~^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\deth_\Carmel Capital\TECNOLOGIA - Geral\DESENVOLVIMENTO\PYTHON\PROJETOS_EM_DESENVOLVIMENTO\gerenciador_de_estoque\pages\pagina_estoque.py", line 5, in <module>
    from classes.analise_estoque import AnaliseEstoque