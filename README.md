# 📄 Gerenciador de Estoque & Ecossistema CNAB 444

Este ecossistema financeiro é uma plataforma modular desenvolvida em **Python** e **Streamlit**, projetada para automatizar o ciclo completo de recebíveis: desde a geração de remessas e validação de arquivos até a análise de risco (PDD) e gestão de estoque de títulos.

---

## 🚀 Módulos e Páginas (Interface Streamlit)

O projeto é dividido em páginas especializadas para cada etapa da operação:

### 🏦 Remessas e CNAB
*   **Gerador de Remessa (`gerador_remessa.py`):** Interface para converter planilhas Excel no padrão CNAB 444, com seleção dinâmica de fundos e edição de ocorrências.
*   **Validador de CNAB (`validador_cnab.py`):** Leitor técnico de arquivos `.REM` ou `.RET`. Agora com **Inteligência Financeira**: detecta automaticamente se o arquivo é de Cessão ou Liquidação, calcula taxas implícitas (a.m. e a.a.) por título e permite simular o impacto de novas taxas no Valor Presente (VP).

### 📈 Análise de Risco e Carteira
*   **Cálculo de PDD (`calcular_pdd.py`):** Interface para processamento de arquivos de histórico e cálculo automático de Provisão para Devedores Duvidosos (PDD) baseada em atrasos.
*   **Página de Estoque (`pagina_estoque.py`):** Visualização gerencial da carteira atual, permitindo filtros por cedente, vencimento e status.
*   **Página de Liquidados (`pagina_liquidados.py`):** Relatório detalhado de títulos liquidados, ideal para conciliação bancária e análise de performance.

### 💰 Análise Operacional de Recebíveis
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
*   **`AnaliseEstoque`**: Classe orquestradora (Facade) que coordena o processamento de grandes volumes de dados de carteira.
    *   **`ChunkReader`**: Motor de leitura otimizada em chunks para CSV, Excel e ZIP.
    *   **`MetricasAggregator`**: Centraliza o cálculo de KPIs, tickets médios e medianas de rentabilidade.
    *   **`ExcelExporter`**: Gerencia a geração de relatórios formatados em `.xlsx`.
*   **`AnalisePDD`**: Implementa as regras de provisionamento financeiro, transformando dias de atraso em valores de reserva técnica.
*   **`AnaliseCNAB`**: Motor de análise financeira para arquivos CNAB.
    *   **Taxa de Equilíbrio (Breakeven)**: Calcula a taxa exata que iguala o montante da carteira via método iterativo.
    *   **Simulação de Impacto**: Projeta variações no Valor Presente baseadas em mudanças de taxa.
    *   **Conversão Temporal**: Traduz taxas entre as bases mensal (a.m.) e anual (a.a.).

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
│   ├── pagina_liquidacoes.py    # Análise de recebíveis liquidados  
│   ├── pagina_aquisicao.py      # Análise de pipeline de aquisições 
│   └── classificar_historico.py # Classificação de dados brutos
├── src/                         # Core da Aplicação
│   ├── classes/                 # Motores de Cálculo e Conversores
│   │   ├── analise_estoque.py   # Orquestrador da análise de carteira
│   │   ├── chunk_reader.py      # Leitor de dados em chunks 
│   │   ├── metricas_aggregator.py # Calculador de métricas 
│   │   ├── excel_exporter.py    # Exportador de relatórios 
│   │   ├── analise_pdd.py       # Cálculo de risco
│   │   ├── cnab444_converter.py
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

### v — 08/05/2026

#### Refatoração da Análise de Estoque
- **Decomposição Modular**: A classe `AnaliseEstoque` foi refatorada para o padrão Facade, delegando responsabilidades para `ChunkReader`, `MetricasAggregator` e `ExcelExporter`.
- **Melhoria de Manutenibilidade**: Redução de complexidade no motor principal e isolamento da lógica de leitura e exportação.

#### Inteligência Financeira em CNABs
- **Novo Módulo `analise_cnab.py`**: Motor matemático para auditoria de taxas e simulações financeiras.
- **Auditoria de Taxas no Validador**: Exibição de taxas implícitas individuais por título em base mensal e anual.
- **Cálculo de Breakeven**: Implementação de busca iterativa para encontrar a taxa de equilíbrio real da carteira (precisão de 4 casas decimais).
- **Simulador de Taxas**: Ferramenta interativa para projetar o impacto de novos deságios no Valor Presente Total.
- **Automação de Finalidade**: O sistema detecta automaticamente se o arquivo é de **Cessão** ou **Liquidação** analisando as ocorrências e códigos de baixa.
- **Base de Cálculo Flexível**: Ajuste para utilizar a Data da Operação (Header) como referência temporal única.

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
