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