# 📄 Gerenciador de Estoque & Ecossistema CNAB 444

Este ecossistema financeiro é uma plataforma modular desenvolvida em **Python** e **Streamlit**, projetada para automatizar o ciclo completo de recebíveis: desde a geração de remessas e validação de arquivos até a análise de risco (PDD) e gestão de estoque de títulos.

---

## 🚀 Módulos e Páginas (Interface Streamlit)

O projeto é dividido em páginas especializadas para cada etapa da operação:

### 🏦 Remessas e CNAB
*   **Gerador de Remessa (`gerador_remessa.py`):** Interface para converter planilhas Excel no padrão CNAB 444, com seleção dinâmica de fundos e edição de ocorrências.
*   **Validador de CNAB (`validador_cnab.py`):** Leitor técnico de arquivos `.REM` ou `.RET`, apresentando KPIs financeiros e tradução de códigos bancários.

### 📈 Análise de Risco e Carteira
*   **Cálculo de PDD (`calcular_pdd.py`):** Interface para processamento de arquivos de histórico e cálculo automático de Provisão para Devedores Duvidosos (PDD) baseada em atrasos.
*   **Página de Estoque (`pagina_estoque.py`):** Visualização gerencial da carteira atual, permitindo filtros por cedente, vencimento e status.
*   **Página de Liquidados (`pagina_liquidados.py`):** Relatório detalhado de títulos liquidados, ideal para conciliação bancária e análise de performance.

### 💰 Análise Operacional de Recebíveis *(Novo)*
*   **Análise de Liquidações (`pagina_liquidacoes.py`):** Dashboard para análise de recebíveis liquidados. Suporta upload de ZIP, CSV e XLSX. Exibe KPIs globais (valor de aquisição, vencimento, pago e retorno), agrupamentos por situação, cedente, mês de vencimento e mês de aquisição. Inclui mapeamento automático de nomes alternativos de colunas e proteção robusta contra colunas duplicadas.
*   **Análise de Aquisições (`pagina_aquisicao.py`):** Dashboard para análise do pipeline de aquisições. Apresenta KPIs de deságio, breakdown por tipo de recebível, ranking dos top 20 sacados, e evolução mensal por data de entrada e vencimento. Mesmo mecanismo de normalização de colunas da página de liquidações.

### 📂 Processamento de Dados
*   **Classificador de Histórico (`classificar_historico.py`):** Ferramenta para categorizar movimentações brutas de extratos ou arquivos de sistema em categorias de negócio. Recursos recentes:
    *   **Formatação de datas:** detecção automática da coluna de data, geração de coluna de referência `01/mm/aaaa` ao lado da data original e exportação no padrão brasileiro `dd/mm/aaaa`.
    *   **Ordenação de colunas:** a coluna `Saldo` é sempre movida para a última posição no arquivo Excel exportado.

---

## 🛠️ Arquitetura do Sistema (Classes Core)

A lógica de negócio está encapsulada em classes robustas dentro de `src/classes/`:

### 🏗️ Motores de Conversão
*   **`CNAB444Converter`:** O motor principal de geração. Utiliza o padrão POO para montar registros de Header, Detalhe e Trailer com validação de tamanho de linha.
*   **`CNABParserFactory`:** Implementa o padrão *Factory* para detectar automaticamente qual banco/layout deve ser usado para ler um arquivo CNAB.
*   **`SingulareParser`:** Especialização do leitor para o layout da administradora Singulare.

### 📐 Inteligência de Negócio
*   **`AnaliseEstoque`:** Classe responsável por realizar cálculos complexos sobre a carteira, como agrupamentos por cedente e cálculos de duration.
*   **`AnalisePDD`:** Implementa as regras de provisionamento financeiro, transformando dias de atraso em valores de reserva técnica.

### 🔧 Utilitários
*   **`Formater`:** Classe central de formatação. Centraliza a lógica de limpeza de documentos (CPF/CNPJ), formatação de moedas e padronização de datas para o padrão bancário.

---

## 📁 Estrutura do Projeto

```text
├── pages/                       # Interface do Usuário (Streamlit)
│   ├── gerador_remessa.py       # Geração de remessas CNAB
│   ├── validador_cnab.py        # Leitura e auditoria de CNAB
│   ├── calcular_pdd.py          # Cálculo de provisão (risco)
│   ├── pagina_estoque.py        # Dashboard de títulos ativos
│   ├── pagina_liquidacoes.py    # Análise de recebíveis liquidados  ← NOVO
│   ├── pagina_aquisicao.py      # Análise de pipeline de aquisições ← NOVO
│   └── classificar_historico.py # Classificação de dados brutos
├── src/                         # Core da Aplicação
│   ├── classes/                 # Motores de Cálculo e Conversores
│   │   ├── cnab444_converter.py
│   │   ├── AnalisePDD.py
│   │   ├── SingulareParser.py
│   │   └── Formater.py
│   ├── components/
│   │   └── selector.py          # Componente genérico de upload
│   ├── data_loader.py           # Leitores de ZIP, CSV e XLSX
│   └── global_var.py            # Central de constantes e mapas
├── models/                      # Modelos ML treinados (.joblib)
├── notebooks/
│   └── criacao_modelos.py       # Script de treino do classificador
├── config_fundos.json           # Dados reais dos fundos (SECRETO)
├── config_fundos_example.json   # Modelo para novos usuários
└── app.py                       # Launcher da aplicação
```

---

## 🛠️ Tecnologias Utilizadas

*   **Linguagem:** Python 3.12+
*   **Interface:** Streamlit (UI Moderna e Reativa)
*   **Processamento:** Pandas (Dataframes)
*   **Arquitetura:** Programação Orientada a Objetos (POO)
*   **Testes:** Pytest para validação de layout e formatadores.

---

## 🔒 Segurança e Boas Práticas

*   **Proteção de Segredos:** Arquivos com dados sensíveis (`.env`, `config_fundos.json`) estão protegidos via `.gitignore`.
*   **Upload Dinâmico:** Em ambientes de nuvem, é possível subir o JSON de configuração diretamente pela interface para manter os dados apenas na memória da sessão.
*   **Extensibilidade:** O sistema permite adicionar novos bancos apenas criando uma nova classe que herde de `CNABParser`.

---

## 📋 Como Utilizar

### Instalação
1. Clone o repositório e instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Execução
```bash
streamlit run app.py
```

### Configuração dos Fundos
1. Utilize o arquivo `config_fundos_example.json` como modelo.
2. Crie um arquivo `config_fundos.json` com os dados reais dos seus fundos.
3. Se preferir, suba o JSON diretamente pela barra lateral da página "Gerador de Remessa".

---

## 🧪 Testes
Para garantir a integridade do layout CNAB:
```bash
pytest tests/unit/
```

---

## 📝 Changelog

### v — 06/05/2026

#### Novas páginas
- **`pagina_liquidacoes.py`** — Dashboard de análise de recebíveis liquidados com KPIs, agrupamentos e filtros. Suporta ZIP, CSV e XLSX. Inclui mapeamento de aliases de colunas e proteção tripla contra colunas duplicadas.
- **`pagina_aquisicao.py`** — Dashboard de análise de aquisições com deságio, ranking de sacados e evolução mensal. Mesma robustez de normalização de colunas.

#### Melhorias no Classificador de Histórico
- Detecção automática da coluna de data.
- Nova coluna de referência `<Data>_Ref` com o dia fixo em `01` (`01/mm/aaaa`).
- Data original exportada no padrão brasileiro (`dd/mm/aaaa`) no Excel.
- Coluna `Saldo` movida automaticamente para a última posição no download.

#### Correção de layout
- Resolvido conflito de `st.set_page_config` que impedia o modo widescreen de carregar imediatamente.

---
*Desenvolvido por Lucas Martins para Carmel Capital.*
