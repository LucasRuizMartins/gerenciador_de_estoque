COLUNAS_ESTOQUE = list(['NOME_FUNDO',
           'DOC_FUNDO',
           'NOME_CEDENTE',
           'DOC_CEDENTE',
           'NOME_SACADO',
           'DOC_SACADO',
           'TIPO_RECEBIVEL',
           'VALOR_NOMINAL',
           'VALOR_PRESENTE',
           'VALOR_AQUISICAO',
           'VALOR_PDD',
           'DATA_VENCIMENTO_AJUSTADA',
           'DATA_EMISSAO',
           'DATA_AQUISICAO',
           'NU_DOCUMENTO',
           'SEU_NUMERO',
           'PRAZO',
           'PRAZO_ATUAL',
           'FAIXA_PDD'
          ])


MAP_CEDENTE = {'01':'pessoa fisica', '02':'pessoa juridica'}

MAP_OCORRENCIA = {
    '01': 'Remessa - Aquisição de títulos',
    '04': 'Abatimento',
    '06': 'Alteração de vencimento',
    '11': 'Aquisição de contratos futuros',
    '12': 'Aquisição de conciliação de contratos futuros',
    '14': 'Pagamento parcial',
    '71': 'Baixa por recompra (Liq. Consultoria)',
    '72': 'Recompra parcial sem adiantamento',
    '73': 'Recompra parcial com adiantamento',
    '74': 'Baixa por recompra (Liq. Cedente)',
    '75': 'Baixa por depósito cedente',
    '76': 'Baixa por depósito consultoria',
    '77': 'Baixa por depósito sacado',
    '80': 'Remessa - Aquisição (Liq. Consultoria)',
    '81': 'Entrada por recompra (Troca - Liq. Consultoria)',
    '84': 'Entrada por recompra (Troca - Liq. Cedente)',
    '87': 'Reativação'
}


MAP_ESPECIE_TITULO = {
    1: "Duplicata",
    2: "Nota Promissória",
    3: "Nota de Seguro",
    4: "Cobrança Seriada",
    5: "Recibo",
    10: "Letras de Câmbio",
    11: "Nota de Débito",
    13: "Precatórios",
    14: "Duplicata de Serviço Físico",
    21: "Renegociação da Dívida",
    41: "CCB Digital",
    50: "NF - Nota Fiscal",
    51: "Cheque",
    52: "Cheque - Manual",
    60: "Contrato",
    61: "Contrato Físico",
    62: "Confissão de Dívida",
    64: "Assunção de Dívida",
    65: "Fatura de Cartão de Crédito",
    70: "CCB Pré Digital",
    71: "CCB Pré Balcão",
    72: "CCB Pré Cetip",
    73: "Outros",
    74: "CCB - Formalização Fonada",
    87: "Cheque"
}