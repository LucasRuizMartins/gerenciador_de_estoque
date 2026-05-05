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

### 📂 Processamento de Dados
*   **Classificador de Histórico (`classificar_historico.py`):** Ferramenta para categorizar movimentações brutas de extratos ou arquivos de sistema em categorias de negócio.

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
├── pages/                  # Interface do Usuário (Streamlit)
│   ├── gerador_remessa.py  # Geração de remessas CNAB
│   ├── validador_cnab.py   # Leitura e auditoria de CNAB
│   ├── calcular_pdd.py     # Cálculo de provisão (risco)
│   ├── pagina_estoque.py   # Dashboard de títulos ativos
│   └── classificar_historico.py # Classificação de dados brutos
├── src/                    # Core da Aplicação
│   ├── classes/            # Motores de Cálculo e Conversores
│   │   ├── cnab444_converter.py
│   │   ├── AnalisePDD.py
│   │   ├── SingulareParser.py
│   │   └── Formater.py
│   └── global_var.py       # Central de constantes e mapas
├── config_fundos.json      # Dados reais dos fundos (SECRETO)
├── config_fundos_example.json # Modelo para novos usuários
└── app.py                  # Launcher da aplicação
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
*Desenvolvido por Lucas Martins para Carmel Capital.*
