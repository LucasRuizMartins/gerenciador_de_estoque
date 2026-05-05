# Documentação Técnica: Suíte de Testes Automatizados

Esta documentação detalha a estrutura, os objetivos e a utilização dos testes automatizados implementados no projeto **Gerenciador de Estoque**. O objetivo é garantir a integridade dos cálculos financeiros e a robustez do processamento de dados.

## 1. Arquitetura de Testes

Utilizamos o framework **Pytest**, que é o padrão da indústria para Python, devido à sua simplicidade e capacidade de escala.

### Estrutura de Diretórios
```text
gerenciador_de_estoque/
├── tests/
│   ├── conftest.py           # Fixtures (dados de exemplo reutilizáveis)
│   └── unit/                 # Testes unitários de lógica isolada
│       ├── test_analise_pdd.py
│       ├── test_data_loader.py
│       └── test_tdd_demo.py
├── pyproject.toml            # Configuração do ambiente de teste
└── testar.ps1                # Atalho para execução no Windows
```

---

## 2. Detalhamento dos Testes Implementados

### A. Lógica de PDD (`test_analise_pdd.py`)
Focado em garantir que os cálculos de Provisão para Devedores Duvidosos (PDD) sigam as regras de negócio.

*   **Situações de Erro Cobertas:**
    *   **Categorização de Prazos:** Garante que valores negativos (atraso) caiam na faixa correta e valores positivos fiquem como "A vencer".
    *   **Limites de Faixa:** Testa se o sistema respeita os limites superiores e inferiores das tabelas de configuração.
    *   **Agregação de Dados:** Verifica se a função de processamento totaliza os valores corretamente (ex: soma de Valor Presente) sem perder registros.
    *   **Bug de Coluna Inexistente:** O teste detectou que o código falhava se tentasse filtrar a coluna `FAIXA_PDD` antes dela ser criada. Isso foi corrigido.

### B. Carregamento de Dados (`test_data_loader.py`)
Focado na entrada de dados via arquivos CSV e ZIP.

*   **Situações de Erro Cobertas:**
    *   **Parsing de Decimais:** Garante que números formatados como texto (ex: `100,50`) sejam convertidos corretamente para float (`100.5`).
    *   **Codificação (Encoding):** Verifica se arquivos com caracteres especiais (ISO-8859-1) são lidos sem erros de codificação.
    *   **Arquivos Vazios:** Garante que o sistema não "quebre" ao tentar ler um arquivo que só possui o cabeçalho.
    *   **Mocks de Arquivo:** Utilizamos `BytesIO` para simular arquivos em memória, evitando a necessidade de criar arquivos físicos para testar.

### C. Demonstração de TDD (`test_tdd_demo.py`)
Utilizado para validar funções de utilidade e servir como guia de aprendizado.

*   **Funcionalidades:**
    *   **Limpeza de Strings:** Testa a função `limpar_cpf_cnpj`, garantindo que pontuações, espaços e caracteres especiais sejam removidos, mantendo apenas dígitos.

---

## 3. Padrões Utilizados (Boas Práticas)

1.  **Padrão AAA (Arrange, Act, Assert):**
    *   **Arrange (Organizar):** Preparação dos dados e mocks.
    *   **Act (Agir):** Execução da função a ser testada.
    *   **Assert (Garantir):** Verificação se o resultado é o esperado.
2.  **Fixtures:** Localizadas em `conftest.py`, são funções que geram dados de teste automaticamente para os outros arquivos, evitando repetição de código (DRY - Don't Repeat Yourself).
3.  **Mocks:** Simulação de objetos complexos (como arquivos) para isolar o teste da dependência do sistema de arquivos ou rede.

---

## 4. Como Executar os Testes

### No Windows (PowerShell):
Use o atalho criado:
```powershell
./testar.ps1
```

### Via Terminal (Qualquer OS):
```bash
pytest tests/unit
```

---

## 5. Guia para TDD (Test-Driven Development)

Para suas novas funcionalidades, siga este fluxo:

1.  **Vermelho (FALHA):** Crie um arquivo `test_minha_feature.py` e escreva o teste de como a função *deveria* funcionar. Rode o teste e veja ele falhar.
2.  **Verde (PASSOU):** Escreva o código mínimo na sua aplicação para que o teste passe.
3.  **Refatorar:** Melhore a qualidade do código. O teste garantirá que você não quebrou nada durante a melhoria.

> [!TIP]
> Sempre que encontrar um erro (Bug) no seu programa, crie primeiro um teste que reproduza esse erro. Só depois corrija o código. Isso garante que aquele erro nunca mais voltará!
