# FIDC – Fundo de Investimentos de Direitos Creditórios
## Troca Eletrônica Padrão – Cobrança Remessa V3
> Revisado: 17/07/2025

---

## Sumário

1. [Introdução](#1-introdução)
   - 1.1 [Serviços Permitidos](#11-serviços-permitidos)
   - 1.2 [Nomenclatura do Arquivo Remessa](#12-nomenclatura-do-arquivo-remessa)
   - 1.3 [Regras para Preenchimento dos Campos](#13-regras-para-preenchimento-dos-campos)
2. [Registro Header](#2-registro-header)
   - 2.1 [Descrição dos Campos](#21-descrição-dos-campos)
3. [Registro Detalhe](#3-registro-detalhe)
   - 3.1 [Descrição dos Campos](#31-descrição-dos-campos)
4. [Registro Pagamento (Opcional)](#4-registro-pagamento-opcional)
5. [Registro Trailer](#5-registro-trailer)

---

## 1. Introdução

### 1.1 Serviços Permitidos

Os serviços permitidos no sistema de FIDC por processamento direto padronizado (CNAB) são:

- **Entrada de títulos**
- **Instruções**

---

### 1.2 Nomenclatura do Arquivo Remessa

O nome do arquivo de remessa deve seguir o padrão:

```
CBDDMMxx.REM  ou  CBDDMMxx.TXT
```

| Componente | Descrição |
|---|---|
| `CB` | Caracteres fixos |
| `DD` | Dia de geração do arquivo |
| `MM` | Mês de geração do arquivo |
| `xx` | Variáveis alfanuméricas (ex.: `01`, `AE`, `E1`) |
| `.REM` / `.TXT` | Extensão do arquivo |

**Exemplos:**
```
CB230501.REM  |  CB2305AE.REM  |  CB2305E1.REM
CB230501.TXT  |  CB2305AE.TXT  |  CB2305E1.TXT
```

---

### 1.3 Regras para Preenchimento dos Campos

| Tipo de campo | Regra |
|---|---|
| **Numérico** | Alinhado à **direita**; posições não preenchidas recebem `0` (zeros) à esquerda |
| **Alfanumérico** | Alinhado à **esquerda**; posições não preenchidas recebem espaços em branco à direita |
| **Não preenchido** | Preencher com zeros |
| **Maiúsculas** | Todos os caracteres em maiúsculo; não são permitidos caracteres especiais (`Ç`, `@`, etc.) nem acentuados (`Á`, `É`, `Ê`, etc.) |
| **Valores monetários** | 2 casas decimais **sem** pontuação ou vírgula |

**Exemplo de formatação monetária:**

| Campo | Formato | Valor no arquivo | Valor formatado |
|---|---|---|---|
| Valor da parcela | `9(015)` | `000000000247056` | R$ 2.470,56 |

> **Notação:** `X(k)` indica campo alfanumérico de `k` caracteres; `9(k)` indica campo numérico de `k` dígitos.

---

## 2. Registro Header

> Identificação do registro: `0` | Tamanho total do registro: **444 posições**

| Num | Nome do Campo | Início | Fim | Tam. | Obrig. | Tipo | Dec. | Conteúdo |
|---|---|---|---|---|---|---|---|---|
| 1 | Identificação do Registro | 1 | 1 | 001 | Sim | `9(1)` | — | `0` |
| 2 | Identificação do Arquivo Remessa | 2 | 2 | 001 | Sim | `9(1)` | — | `1` |
| 3 | Literal Remessa | 3 | 9 | 007 | Sim | `X(7)` | — | `REMESSA` |
| 4 | Código de Serviço | 10 | 11 | 002 | Sim | `9(2)` | — | `01` |
| 5 | Literal Serviço | 12 | 26 | 015 | Sim | `X(15)` | — | `COBRANCA` |
| 6 | Código do Originador (Consultoria) | 27 | 46 | 020 | Sim | `9(20)` | — | Fornecido pelo Custodiante no cadastramento *(ver 2.1-A)* |
| 7 | Nome do Originador (Consultoria) | 47 | 76 | 030 | Sim | `X(30)` | — | Razão Social |
| 8 | Número do Banco | 77 | 79 | 003 | Sim | `9(3)` | — | Número do Banco |
| 9 | Nome do Banco | 80 | 94 | 015 | Sim | `X(15)` | — | Nome do Banco |
| 10 | Data da Gravação do Arquivo | 95 | 100 | 006 | Sim | `9(6)` | — | `DDMMAA` *(ver 2.1-B)* |
| 11 | Branco | 101 | 108 | 008 | Sim | `X(8)` | — | Branco |
| 12 | Identificação do Sistema | 109 | 110 | 002 | Sim | `X(2)` | — | `MX` |
| 13 | Nº Sequencial do Arquivo | 111 | 117 | 007 | Sim | `9(7)` | — | Sequencial |
| 14 | Número do Banco (cedente) | 118 | 120 | 003 | Não | `9(3)` | — | Número do banco do cedente |
| 15 | Número da Agência do Banco | 121 | 125 | 005 | Não | `9(5)` | — | Agência do Cedente |
| 16 | Dígito Verificador da Agência | 126 | 126 | 001 | Não | `9(1)` | — | Dígito verificador da agência do cedente |
| 17 | Número da Conta Corrente | 127 | 138 | 012 | Não | `9(12)` | — | Número da conta corrente do cedente |
| 18 | Dígito Verificador da Conta Corrente | 139 | 139 | 001 | Não | `9(1)` | — | Dígito verificador da conta corrente |
| 19 | Branco | 140 | 438 | 299 | Sim | `X(299)` | — | Branco |
| 20 | Nº Sequencial do Registro | 439 | 444 | 006 | Sim | `9(6)` | — | `000001` |

### 2.1 Descrição dos Campos

**A – Campo 6 (Código do Originador):** Será informado pelo Custodiante no momento do cadastramento na Custódia.

**B – Campo 10 (Data da Gravação do Arquivo):** Data do dia da operação, no formato `DDMMAA`.

---

## 3. Registro Detalhe

> Identificação do registro: `1` | Tamanho total do registro: **444 posições**

| Num | Nome do Campo | Início | Fim | Tam. | Obrig. | Tipo | Dec. | Conteúdo |
|---|---|---|---|---|---|---|---|---|
| 1 | Identificação do Registro | 1 | 1 | 001 | Sim | `9(1)` | — | `1` |
| 2 | Data de Carência | 2 | 7 | 006 | Não | `9(6)` | — | `DDMMAA` – Data de carência |
| 3 | Tipo de Juros | 8 | 8 | 001 | Não | `9(1)` | — | `0`=Sem correção; `1`=Juros Fixo; `2`=CDI; `3`=IPCA-15; `4`=IPCA; `5`=IGPM |
| 4 | Branco | 9 | 10 | 002 | Não | `X(2)` | — | Branco |
| 5 | Taxa de Juros | 11 | 20 | 010 | Não | `9(10)` | 7 | Juros para correção do título (fixo ou % do indexador) |
| 6 | Coobrigação | 21 | 22 | 002 | Sim | `9(2)` | — | `01`=Com coobrigação; `02`=Sem coobrigação |
| 7 | Característica Especial | 23 | 24 | 002 | Sim (renegociação CCB) | `9(2)` | — | Src3040 BACEN – ver Anexo 8 |
| 8 | Modalidade da Operação | 25 | 28 | 004 | Sim (CCB) | `9(4)` | — | Src3040 BACEN – domínio + subdomínio – ver Anexo 3 |
| 9 | Natureza da Operação | 29 | 30 | 002 | Sim (CCB) | `9(2)` | — | Src3040 BACEN – ver Anexo 2 |
| 10 | Origem do Recurso | 31 | 34 | 004 | Não | `9(4)` | — | Src3040 BACEN – domínio + subdomínio – ver Anexo 4 |
| 11 | Classe Risco da Operação | 35 | 36 | 002 | Não | `X(2)` | — | Src3040 BACEN – preencher da esquerda para direita – ver Anexo 17 |
| 12 | Zeros | 37 | 37 | 001 | Não | `9(1)` | — | `0` |
| 13 | Nº de Controle do Participante | 38 | 62 | 025 | Sim | `X(25)` | — | ID do título na consultoria (mesmo informado ao banco cobrador) |
| 14 | Número do Banco (cheque) | 63 | 65 | 003 | Sim (cheque) | `9(3)` | — | Número do banco pertencente ao cheque |
| 15 | Zeros | 66 | 70 | 005 | Sim | `9(5)` | — | `00000` |
| 16 | Identificação do Título no Banco | 71 | 81 | 011 | Não | `9(11)` | — | Branco |
| 17 | Dígito do Nosso Número | 82 | 82 | 001 | Não | `X(1)` | — | Branco |
| 18 | Valor Pago | 83 | 92 | 010 | Sim (liquidação) | `9(10)` | 2 | Valor pago; zeros se não for ocorrência de liquidação |
| 19 | Condição para Emissão da Papeleta | 93 | 93 | 001 | Não | `X(1)` | — | Branco |
| 20 | Ident. Débito Automático | 94 | 94 | 001 | Não | `X(1)` | — | Branco |
| 21 | Data da Liquidação | 95 | 100 | 006 | Sim (liquidação) | `9(6)` | — | `DDMMAA` – somente para liquidação do título |
| 22 | Número da Duplicata | 101 | 104 | 004 | Sim (duplicata) | `X(4)` | — | Branco |
| 23 | Indicador Rateio Crédito | 105 | 105 | 001 | Não | `X(1)` | — | Branco |
| 24 | Endereçamento para Aviso de Débito | 106 | 106 | 001 | Não | `X(1)` | — | Branco |
| 25 | Branco | 107 | 108 | 002 | Não | `X(2)` | — | Branco |
| 26 | Identificação Ocorrência | 109 | 110 | 002 | Sim | `9(2)` | — | *Ver seção 3.1-A* |
| 27 | Nº do Documento | 111 | 120 | 010 | Sim | `X(10)` | — | Número do documento |
| 28 | Data do Vencimento do Título | 121 | 126 | 006 | Sim | `9(6)` | — | `DDMMAA` |
| 29 | Valor do Título (face / nominal) | 127 | 139 | 013 | Sim | `9(13)` | 2 | Valor nominal do título |
| 30 | Banco Encarregado da Cobrança | 140 | 142 | 003 | Não | `9(3)` | — | Nº do banco na câmara de compensação |
| 31 | Agência Depositária | 143 | 147 | 005 | Não | `9(5)` | — | Código da agência depositária |
| 32 | Espécie de Título | 148 | 149 | 002 | Sim | `9(2)` | — | *Ver seção 3.1-E* |
| 33 | Identificação | 150 | 150 | 001 | Não | `X(1)` | — | Branco |
| 34 | Data da Emissão do Título | 151 | 156 | 006 | Sim | `9(6)` | — | `DDMMAA` |
| 35 | 1ª Instrução | 157 | 158 | 002 | Não | `9(2)` | — | `00` |
| 36 | 2ª Instrução | 159 | 159 | 001 | Não | `9(1)` | — | `0` |
| 37 | Tipo de Pessoa do Cedente | 160 | 161 | 002 | Sim | `X(2)` | — | `01`=Pessoa física; `02`=Pessoa jurídica |
| 38 | Juros/Mora | 162 | 173 | 012 | Não | `X(12)` | 7 | Juros a cobrar por dia de atraso |
| 39 | Número do Termo de Cessão | 174 | 192 | 019 | Sim | `X(19)` | — | Conforme número enviado pela consultoria |
| 40 | Valor Presente da Parcela (Aquisição) | 193 | 205 | 013 | Sim | `9(13)` | 2 | Valor da parcela na data de cessão (valor de aquisição) |
| 41 | Valor do Abatimento | 206 | 218 | 013 | Não | `9(13)` | 2 | Valor do abatimento a ser concedido na instrução |
| 42 | Identificação do Tipo de Inscrição do Sacado | 219 | 220 | 002 | Sim | `9(2)` | — | `01`=Pessoa física; `02`=Pessoa jurídica |
| 43 | Nº Inscrição do Sacado (CPF/CNPJ) | 221 | 234 | 014 | Sim | `9(14)` | — | CPF ou CNPJ |
| 44 | Nome do Sacado | 235 | 274 | 040 | Sim | `X(40)` | — | Nome do sacado |
| 45 | Endereço Completo | 275 | 314 | 040 | Sim | `X(40)` | — | Endereço do sacado |
| 46 | Número da Nota Fiscal da Duplicata | 315 | 323 | 009 | Sim (duplicata) | `X(9)` | — | Número da nota fiscal da duplicata |
| 47 | Número da Série da NF da Duplicata | 324 | 326 | 003 | Sim (duplicata) | `X(3)` | — | Número da série da nota fiscal da duplicata |
| 48 | CEP | 327 | 334 | 008 | Sim | `9(8)` | — | CEP do sacado |
| 49 | Cedente | 335 | 394 | 060 | Sim | `X(60)` | — | Decomposição – *ver seção 3.1-D* |
| 50 | Chave da Nota / IPOC | 395 | 438 | 044 | Sim (duplicata/CCB) | `X(44)` | — | Chave da NF-e (duplicatas) ou IPOC (CCBs) |
| 51 | Nº Sequencial do Registro | 439 | 444 | 006 | Sim | `9(6)` | — | Número sequencial do registro |

### 3.1 Descrição dos Campos

#### A – Campo 26: Identificação de Ocorrência

| Código | Descrição |
|---|---|
| `01` | Remessa – aquisição de títulos |
| `04` | Abatimento (mediante justificativa) – valor em posições 206–218 |
| `06` | Alteração de vencimento (somente para conciliação; não altera o original) |
| `14` | Pagamento parcial – valor pago em posições 83–92 |
| `71` | Baixa por recompra / novo título **com liquidação para a consultoria** – exige contrapartida `81` no mesmo arquivo |
| `72` | Recompra parcial sem adiantamento |
| `73` | Recompra parcial com adiantamento |
| `74` | Baixa por recompra / novo título **com liquidação para o cedente** – exige contrapartida `84` no mesmo arquivo |
| `75` | Baixa por depósito cedente |
| `76` | Baixa por depósito consultoria |
| `77` | Baixa por depósito sacado |
| `80` | Remessa – aquisição de títulos (com liquidação para a consultoria) |
| `81` | Entrada por recompra/troca de títulos, com liquidação para a consultoria – exige contrapartida `71` no mesmo arquivo |
| `84` | Entrada por recompra/troca de títulos, com liquidação para o cedente – exige contrapartida `74`; usar código `84` para recompras internas |
| `87` | Reativação |
| `11` | Aquisição de contratos futuros |
| `12` | Aquisição de conciliação de contratos futuros |

#### B – Campo 13: Nº de Controle do Participante

Considerado como número de identificação do título no banco. Deve ser preenchido da **esquerda para a direita**.

#### C – Campo 43: Nº de Inscrição do Sacado

Quando se tratar de CNPJ, adotar o critério de preenchimento da **direita para a esquerda**.

#### D – Campo 49: Cedente – Decomposição do Campo

| Posições | Conteúdo |
|---|---|
| 335 – 380 | Nome do Cedente |
| 381 – 394 | CNPJ do Cedente |

Preencher da **esquerda para a direita**.

#### E – Campo 32: Espécie de Título

| Código | Descrição |
|---|---|
| `01` | Duplicata |
| `02` | Nota Promissória |
| `03` | Nota de Seguro |
| `04` | Cobrança Seriada |
| `05` | Recibo |
| `06` | Nota Promissória Física |
| `10` | Letras de Câmbio |
| `11` | Nota de Débito |
| `13` | Precatórios |
| `14` | Duplicata de Serviço Físico |
| `21` | Renegociação da Dívida |
| `41` | CCB Digital |
| `50` | NF – Nota Fiscal |
| `51` | Cheque |
| `52` | Cheque Manual |
| `60` | Contrato |
| `61` | Contrato Físico |
| `62` | Confissão de Dívida |
| `64` | Assunção de Dívida |
| `65` | Fatura de Cartão de Crédito |
| `70` | CCB Pré Digital |
| `71` | CCB Pré Balcão |
| `72` | CCB Pré CETIP |
| `73` | Outros |
| `74` | CCB – Formalização Fonada |
| `87` | Cheque |

---

## 4. Registro Pagamento (Opcional)

> Identificação do registro: `2` | Tamanho total do registro: **444 posições**

| Num | Nome do Campo | Início | Fim | Tam. | Obrig. | Tipo | Dec. | Conteúdo |
|---|---|---|---|---|---|---|---|---|
| 1 | Identificação do Registro | 1 | 1 | 001 | Sim | `9(1)` | — | `2` |
| 2 | Tipo de Pagamento | 2 | 20 | 019 | Sim | `X(19)` | — | `CEDENTE` ou `HONORARIO` |
| 3 | Tipo de Cedente | 21 | 22 | 002 | Sim | `9(2)` | — | `01`=Pessoa física; `02`=Pessoa jurídica |
| 4 | Identificação do Cedente | 23 | 36 | 014 | Sim | `9(14)` | — | CPF/CNPJ do cedente |
| 5 | Nome do Cedente | 37 | 82 | 046 | Sim | `X(46)` | — | Nome do cedente |
| 6 | Número do Banco do Cedente | 83 | 85 | 003 | Sim | `9(3)` | — | Número do banco do cedente |
| 7 | Número da Agência do Banco | 86 | 90 | 005 | Sim | `9(5)` | — | Agência do banco do cedente |
| 8 | Dígito Verificador da Agência | 91 | 91 | 001 | Não | `9(1)` | — | Dígito verificador da agência do cedente |
| 9 | Número da Conta Corrente do Cedente | 92 | 103 | 012 | Sim | `9(12)` | — | Número da conta corrente do cedente |
| 10 | Dígito Verificador da Conta Corrente | 104 | 104 | 001 | Não | `9(1)` | — | Dígito verificador da conta corrente |
| 11 | Valor do Pagamento | 105 | 117 | 013 | Sim | `9(13)` | 2 | Valor a ser pago na conta informada |
| 12 | Branco | 118 | 438 | 321 | Sim | `X(321)` | — | Branco |
| 13 | Número Sequencial de Registro | 439 | 444 | 006 | Sim | `9(6)` | — | Nº sequencial do registro |

---

## 5. Registro Trailer

> Identificação do registro: `9` | Tamanho total do registro: **444 posições**

| Num | Nome do Campo | Início | Fim | Tam. | Obrig. | Tipo | Dec. | Conteúdo |
|---|---|---|---|---|---|---|---|---|
| 1 | Identificação do Registro | 1 | 1 | 001 | Sim | `9(1)` | — | `9` |
| 2 | Branco | 2 | 438 | 437 | Sim | `X(437)` | — | Branco |
| 3 | Número Sequencial de Registro | 439 | 444 | 006 | Sim | `9(6)` | — | Nº sequencial do último registro |

---

## Resumo da Estrutura do Arquivo

```
+-----------------------------+
|  HEADER  (tipo 0)           |  1 registro
+-----------------------------+
|  DETALHE (tipo 1)           |  1 por título
|  PAGAMENTO (tipo 2) - opt.  |  1 por pagamento (opcional)
+-----------------------------+
|  TRAILER (tipo 9)           |  1 registro
+-----------------------------+
```

- Tamanho fixo de **444 caracteres** por linha (CNAB 444)
- Cada linha termina com quebra de linha (`\n` ou `\r\n`)
- Todos os registros devem ser numerados sequencialmente no campo de posição 439–444

---

*Documentação gerada com base no layout CNAB444 APEX GROUP V3 – Remessa – revisado em 17/07/2025.*
