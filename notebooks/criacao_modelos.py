"""
Script de Criação e Persistência do Modelo de Classificação de Históricos.
Execute este script sempre que quiser retreinar o modelo com novos dados.
O modelo será salvo em: models/modelo_classificador_YYYY-MM-DD.joblib
#RODAR SCRIPT DE TREINO .\venv\Scripts\python.exe notebooks/criacao_modelos.py
#RODAR O APP ./venv/Scripts/streamlit run app.py
"""

import re
import os
import joblib
import pandas as pd
from datetime import date
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

# CONFIGURAÇÕES

user = os.environ['USERPROFILE']

fundos = {
    'gerar':'gerar',
    'moovpay':'moovpay',
    'fidara':'fidara',
    'virtus':'virtus',
    'sb_II':'sb_II',
    'residence':'residence',
    'housi':'housi',
    'Ene2':'Ene2',
    'cdc':'cdc',
    'apex':'apex',
    'cobuccio_fidc':'cobuccio_fidc'
}
fundo_selecionado = fundos['fidara']

PATH_PLANILHA =   user+ rf'\Carmel Capital\Arquivos - Documentos\00 - CARMEL ASSET\01 - OPERACIONAL\CONTROLADORIA\01 - Relatorios Diarios\Caixa Diario\DADOS_TREINAMENTO\{fundo_selecionado}.xlsx'
COLUNA_HISTORICO = 'Historico'
COLUNA_CATEGORIA = 'Controladoria'
PASTA_MODELOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

# FUNÇÃO DE LIMPEZA DE TEXTO

def limpar_texto(texto: str) -> str:
    """Normaliza o texto do histórico para o padrão esperado pelo modelo."""
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.lower()
    texto = re.sub(r'\d+', '', texto)        # Remove números
    texto = re.sub(r'[^\w\s]', ' ', texto)   # Remove pontuação
    texto = " ".join(texto.split())          # Remove espaços extras
    return texto


# CARREGAMENTO E TRATAMENTO DOS DADOS

print("Carregando dados de treinamento...")
df = pd.read_excel(PATH_PLANILHA, sheet_name='dicionario')

df['Historico_Limpo'] = df[COLUNA_HISTORICO].apply(limpar_texto)
y = df[COLUNA_CATEGORIA].fillna('classificar').astype(str).str.strip()
X = df['Historico_Limpo']

# Remove classes com menos de 2 exemplos (incompatíveis com stratify)

contagem = y.value_counts()
classes_invalidas = contagem[contagem < 2].index

if len(classes_invalidas) > 0:
    print(f"Aviso: Classes removidas por ter apenas 1 exemplo: {list(classes_invalidas)}")
    mascara = ~y.isin(classes_invalidas)
    X = X[mascara]
    y = y[mascara]


# SEPARANDO TREINO E TESTE


X_treino, X_teste, y_treino, y_teste = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)


# CRIANDO E TREINANDO O MODELO

print("Treinando o modelo...")
modelo = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
    ('classificador', LinearSVC(class_weight='balanced', random_state=42))
])
modelo.fit(X_treino, y_treino)


# AVALIAÇÃO

previsoes = modelo.predict(X_teste)
acuracia = accuracy_score(y_teste, previsoes)

print(f"\nTaxa de Acerto (Acurácia): {acuracia * 100:.2f}%\n")
print("--- RELATÓRIO DE CLASSIFICAÇÃO ---")
print(classification_report(y_teste, previsoes))


# SALVANDO O MODELO


os.makedirs(PASTA_MODELOS, exist_ok=True)

nome_arquivo = f"classificador_{fundo_selecionado}.joblib"
caminho_modelo = os.path.join(PASTA_MODELOS, nome_arquivo)

joblib.dump(modelo, caminho_modelo)
print(f"\nModelo salvo com sucesso em: {caminho_modelo}")
