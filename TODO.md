# 🔧 TODO — Refatoração Gerenciador de Estoque

> Auditoria técnica realizada em 07/05/2026.
> Sessão de contexto: `84ac649e-7838-44e5-a19b-61d54f732912`

---

## ✅ Fase 1 — Correções Críticas (CONCLUÍDA)

- [x] Deletar `api.py` (arquivo corrompido com traceback colado)
- [x] Corrigir `analise_estoque.py:78` — exceção silenciada `(f"Erro...")` → `raise`
- [x] Corrigir `analise_estoque.py:238` — `ZeroDivisionError` em `PRAZO=0` → `replace(0, np.nan)`
- [x] Corrigir `analise_estoque.py:1208-1227` — código `salvar()` e `exportar_para_excel()` fora da classe (indentação errada)
- [x] Corrigir `Formater.py` — decoradores inconsistentes (`@classmethod` sem `cls`, métodos sem decorador)
- [x] Corrigir `classificar_historico.py:155` — `mask_ambos_nan` calculado **após** `fillna(0)` (nunca seria True)

## ✅ Fase 2 — Limpeza de Código Morto e Imports (CONCLUÍDA)

- [x] Deletar `pagina_liquidados.py` (stub sem funcionalidade) e remover de `app.py`
- [x] Limpar imports não usados: `plotly.express`, `ZipFile`, `zipfile`, `os`, `data_loader`, `selector` em diversas pages
- [x] Remover variáveis não usadas: `colunas_numericas`, `taxa_anual`
- [x] Substituir todos os `print()` por `logging` em `analise_estoque.py` (9 ocorrências)
- [x] Corrigir typo `CnabPaser.py` → `CnabParser.py` e atualizar imports (`SingulareParser.py`)
- [x] Limpar `data_loader.py`: remover `read_zipfile_from_buffer` (duplicata de `ler_zip`), `agregar_chunks` (anulava chunks carregando tudo na RAM)

## ✅ Fase 3 — Eliminação de Redundâncias / DRY (CONCLUÍDA)

- [x] Criar `src/formatting.py` — módulo centralizado com funções puras (`fmt_moeda`, `fmt_numero`, `fmt_pct`, etc.)
- [x] Refatorar `Formater.py` como **thin wrapper** de retrocompatibilidade, delegando para `src/formatting.py`
- [x] Mover funções compartilhadas para `data_loader.py`: `carregar_arquivo`, `normalizar_colunas`, `aplicar_aliases`, `preparar_colunas_datas`, `preparar_colunas_valores`
- [x] Remover **~170 linhas duplicadas** entre `pagina_aquisicao.py` e `pagina_liquidacoes.py`
- [x] Extrair constantes `FAIXAS_A_VENCER` e `FAIXAS_VENCIDO` como atributos de classe em `AnaliseEstoque`
- [x] Criar `src/components/tables.py` com funções genéricas `agrupar_e_exibir()` e `agrupar_por_mes()`
- [x] Refatorar `pagina_aquisicao.py`: 4 blocos groupby → 4 chamadas declarativas
- [x] Refatorar `pagina_liquidacoes.py`: 4 blocos groupby → 4 chamadas declarativas (com `col_return_pct`)

## ✅ Fase 5 — Melhorias de Performance (CONCLUÍDA)

- [x] Avaliar e remover `gc.collect()` em `analise_estoque.py` (desnecessário com processamento em chunks e `del chunk`)
- [x] Adicionar `type: any` → `type: Any` (de `typing`) em `cnab444_converter.py`
- [x] Substituir `df.iterrows()` por `enumerate(df.to_dict('records'))` em `cnab444_converter.py`
- [x] Remover `agregar_chunks()` de `data_loader.py` (iterava o generator 2x, anulando chunks)

---

## 🔲 Fase 4 — Refatoração SOLID (PENDENTE)

### 4.1 — Decompor `AnaliseEstoque` (God Object — 1200+ linhas)

**Problema**: A classe `AnaliseEstoque` viola SRP — é responsável por leitura de arquivos, processamento em chunks, cálculo de métricas, acumulação de dados, e exportação para Excel. Tudo em 1200 linhas.

**Proposta de decomposição**:

#### `ChunkReader` (nova classe)
- Extrair: `_processar_arquivo_chunks()`, `_obter_chunk_iterator()`, `_processar_csv_chunks()`, `_processar_zip_chunks()`
- Responsabilidade: ler arquivos ZIP/CSV em chunks, preparar cada chunk
- Arquivo: `src/classes/chunk_reader.py`

#### `MetricasAggregator` (nova classe)
- Extrair: `_processar_chunk()`, `_acumular_metricas_globais()`, `_acumular_metricas_mensais()`, `_processar_vencimentos()`, `_finalizar_calculos()`, etc.
- Responsabilidade: receber chunks já preparados, acumular e finalizar métricas
- Arquivo: `src/classes/metricas_aggregator.py`

#### `ExcelExporter` (nova classe)
- Extrair: `exportar_para_excel()`, `_construir_dataframe_relatorio()`, `_obter_valores_totais()`, `_obter_valores_por_tipo()`, `_formatar_planilha_excel()`
- Responsabilidade: exportar as métricas para Excel com formatação
- Arquivo: `src/classes/excel_exporter.py`

#### `AnaliseEstoque` (refatorada)
- Orquestra as 3 classes acima
- Mantém interface pública (`__init__`, `obter_cedentes_agrupados`, `obter_recebiveis_agrupados`)
- Delega: `self.reader = ChunkReader(...)`, `self.aggregator = MetricasAggregator(...)`, etc.

**⚠️ Risco alto**: Esta classe é o core do sistema. Refatorar sem testes unitários é arriscado. Recomendação: escrever testes **antes** de decompor.

### 4.1.1 — Testes unitários para `AnaliseEstoque` (PRÉ-REQUISITO)
- [x] Criar `tests/test_analise_estoque.py` com fixtures de dados de teste
- [x] Testar: métricas globais, métricas por tipo, faixas de vencimento, exportação Excel
- [x] Validar que métricas permanecem idênticas após refatoração
- [x] **EXTRA**: Corrigido bug em `AnaliseEstoque` onde `total_cedentes` e `total_sacados` eram retornados como 0.

### 4.1.2 — Executar decomposição (CONCLUÍDA)
- [x] Criar `src/classes/chunk_reader.py`
- [x] Criar `src/classes/metricas_aggregator.py`
- [x] Criar `src/classes/excel_exporter.py`
- [x] Refatorar `AnaliseEstoque` como orquestrador (Facade)
- [x] Validar interface pública para evitar alteração em `pagina_estoque.py`
- [x] Rodar testes para validar (5/5 testes passando)

---

## ✅ Fase 6 — Melhorias Adicionais (CONCLUÍDA)

### Robustez
- [x] Adicionar `try/except` nos parsers CNAB (`SingulareParser.parse_body`) — Adicionado `_safe_float` e docstrings
- [x] Adicionar validação de colunas em `analise_pdd.py:processar_pdd()` antes de acessar colunas críticas
- [x] Adicionar guard clause em `calcular_pdd.py:54` para evitar `IndexError` em DF vazio

### Padronização
- [x] Remover formatadores duplicados em `AnaliseEstoque` (L.1180-1210) — migrado para `src.formatting`
- [x] Remover `formata_numero()` de `src/funcoes.py` (duplicata)
- [x] Verificar e deletar `mensagem_sucesso()` em `funcoes.py` (não utilizada)

### Configuração e Logging
- [x] Adicionar `logging.basicConfig()` no `app.py` centralizadamente
- [x] Configurar `humanize` locale uma única vez no `app.py`

### Documentação
- [x] Adicionar docstrings nas classes de parser CNAB (`CnabParser`, `SingulareParser`, `CnabParserFactory`)
- [x] Documentar o fluxo de dados: Upload → data_loader → classes → Streamlit display


---

## 📝 Decisões de Arquitetura Tomadas

### Por que `src/formatting.py` com funções puras em vez de classe?
1. **Python idiomático**: classe com apenas `@staticmethod` é um módulo disfarçado
2. **Testabilidade**: funções puras são mais fáceis de testar unitariamente
3. **Retrocompatibilidade**: `Formater` mantido como thin wrapper delegando para as funções
4. **Centralização**: 5 cópias de formatadores → 1 source of truth

### Por que `agrupar_e_exibir()` + `agrupar_por_mes()`?
- Padrão repetido 8x entre 2 pages (groupby → agg → format → rename → display)
- Suporta 2 tipos de ratio: **deságio** `(num-den)/num` e **retorno** `num/den - 1`
- Adição de novas tabelas agrupadas requer apenas 1 chamada declarativa

### Por que `logging` em vez de `print()`?
- `print()` em app Streamlit não é visível ao usuário e polui stdout
- `logging` permite configurar níveis (DEBUG/INFO/WARNING/ERROR) centralizadamente
- Facilita debugging em produção sem modificar código
