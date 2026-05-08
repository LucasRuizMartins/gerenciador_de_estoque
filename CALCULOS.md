# 📖 Dicionário de Cálculos - Gestão de Estoque

Este documento descreve as metodologias e fórmulas utilizadas para gerar os indicadores financeiros apresentados na página de **Análise de Estoque**, seguindo a ordem de visualização do dashboard.

---

## 1. KPIs Principais (Resumo Geral)

### Primeira Linha: Totais Financeiros
*   **Valor Presente Total:** Soma do valor atualizado de todos os títulos, descontando as taxas de cessão pro rata die até a data de hoje.
*   **Valor Nominal Total:** Soma do valor bruto (valor de face) de todos os títulos, sem qualquer desconto ou atualização.
*   **Valor Aquisição Total:** Soma do valor efetivamente pago pelo fundo no momento da compra dos títulos.
*   **PDD (Provisão para Devedores Duvidosos):** Soma dos valores de provisão para perdas informados na base, refletindo o risco de inadimplência.

### Segunda Linha: Status da Carteira
*   **A Vencer:** Soma do **Valor Presente** de todos os títulos que ainda não atingiram a data de vencimento (Prazo >= 0).
*   **Vencido:** Soma do **Valor Presente** de todos os títulos que já ultrapassaram a data de vencimento e não foram liquidados (Prazo < 0).
*   **Total Sacados:** Contagem de CPFs/CNPJs únicos dos sacados (quem paga o título) presentes na base.
*   **Total Cedentes:** Contagem de CPFs/CNPJs únicos dos cedentes (quem vendeu o título para o fundo) presentes na base.

---

## 2. Quantidades (Contagem de Títulos)
*   **Total Títulos:** Quantidade total de documentos/registros processados no arquivo.
*   **Títulos A Vencer:** Quantidade de títulos com data de vencimento futura.
*   **Títulos Vencidos:** Quantidade de títulos com data de vencimento passada.

---

## 3. Aquisições no Mês Atual
Indicadores focados no desempenho do mês referente à data do relatório:
*   **Valor Aquisição no Mês:** Soma do valor pago por todos os títulos comprados dentro do mês atual.
*   **Qtd Aquisição no Mês:** Número total de títulos adquiridos no mês atual.

---

## 4. Performance da Última Quinzena
Filtro que isola os títulos adquiridos nos últimos 15 dias para análise de tendência recente:
*   **VP Total / A Vencer / Vencido:** Valor Presente segmentado dos títulos comprados nos últimos 15 dias.
*   **Aquisição Total / A Vencer / Vencido:** Valor pago segmentado dos títulos comprados nos últimos 15 dias.

---

## 5. Análise de Ticket Médio
Reflete o valor médio por título.
> **Fórmula:** `Soma Total do Valor / Quantidade Total de Títulos`
O sistema apresenta essa visão para:
*   **Valor Presente, Aquisição e Nominal.**
*   Segmentado em: **Total**, **A Vencer** e **Vencido**.
*   Comparativo entre o **Geral** e a **Última Quinzena**.

---

## 6. Prazos Médios e Taxas (Medianas)

### Prazos Médios
Média de dias para o vencimento, **ponderada pelo Valor de Aquisição** (títulos maiores pesam mais no prazo).
*   **Prazo Médio Total:** Média ponderada de dias de toda a carteira.
*   **Prazo Médio A Vencer / Vencido:** Mesma lógica aplicada apenas aos respectivos grupos.

### Medianas e Taxas
*   **Mediana Taxa (Total):** Ponto central das taxas de desconto originais (`TAXA_CESSAO`) informadas no arquivo.
*   **Mediana (A Vencer) / (Vencido):** Ponto central da **Taxa Anualizada (Yield)** calculada pelo sistema para cada grupo.
    > **Yield:** `((Nominal / Aquisição) ^ (252 / Prazo)) - 1 * 100`

---

## 7. Distribuição por Faixas de Vencimento
Tabela que agrupa o **Valor Presente** e o **PDD** conforme a distância do vencimento (em dias):
*   Ex: Faixa `0-15` agrupa títulos que vencem em até 15 dias (se A Vencer) ou estão vencidos há até 15 dias (se Vencido).

---

## 8. Detalhamento por Tipo de Recebível
Permite filtrar todos os indicadores acima (VP, A Vencer, Vencido, PDD, Prazo) para um tipo específico (ex: Cheque, Duplicata).

### Métricas Exclusivas deste Bloco:
*   **Mediana V.A:** Razão entre a Mediana da Taxa Anualizada e a Mediana do Valor de Aquisição (`Taxa / Aquisição`). Reflete a eficiência da taxa capturada por capital alocado.
*   **Mediana Taxa Cessão:** Ponto central da taxa de desconto original para aquele tipo específico.
