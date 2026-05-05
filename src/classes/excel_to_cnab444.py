"""
Conversor Excel -> CNAB 444 (BRL Trust FIDC - Remessa V2)
Layout: Troca Eletrônica Padrão – Cobrança Remessa V2
"""

import pandas as pd
import sys
import os
from datetime import datetime, date


# ──────────────────────────────────────────────
# CONFIGURAÇÕES — ajuste conforme seu cadastro
# ──────────────────────────────────────────────
CONFIG = {
    "codigo_originador": "00000000000000000001",  # 20 dígitos — fornecido pelo Custodiante
    "nome_originador":   "NOME DA CONSULTORIA",   # 30 chars
    "numero_banco":      "173",                    # BRL Trust
    "nome_banco":        "BRLTRUST",               # 15 chars
    "identificacao_sistema": "MX",                 # fixo
    "nr_sequencial_arquivo": 1,                    # incrementar a cada remessa
    "valor_retencao":    0,                        # 10 dígitos
    "codigo_banco_dep":  "173",                    # banco depósito
    "agencia_deposito":  "0001",                   # 4 dígitos
    "conta_corrente":    "00000000000001",          # 14 dígitos
    "coobrigacao":       "01",                     # 01=Com / 02=Sem
    "identificacao_ocorrencia": "01",              # 01=Remessa
}

LINHA_SIZE = 444


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def num(valor, tamanho, decimais=0):
    """Campo numérico: alinhado à direita, zeros à esquerda."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = 0
    if decimais > 0:
        valor = round(float(valor) * (10 ** decimais))
    valor = int(valor)
    return str(valor).zfill(tamanho)[-tamanho:]


def alfa(valor, tamanho):
    """Campo alfanumérico: maiúsculo, sem acento, alinhado à esquerda, espaços à direita."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = ""
    valor = str(valor).upper()
    # Remove acentos simples e caracteres especiais
    replacements = {
        'Á':'A','À':'A','Â':'A','Ã':'A','Ä':'A',
        'É':'E','È':'E','Ê':'E','Ë':'E',
        'Í':'I','Ì':'I','Î':'I','Ï':'I',
        'Ó':'O','Ò':'O','Ô':'O','Õ':'O','Ö':'O',
        'Ú':'U','Ù':'U','Û':'U','Ü':'U',
        'Ç':'C','Ñ':'N',
    }
    for k, v in replacements.items():
        valor = valor.replace(k, v)
    # Remove demais caracteres especiais
    valor = ''.join(c if c.isalnum() or c in ' .-/,' else ' ' for c in valor)
    return valor[:tamanho].ljust(tamanho)


def formata_data(valor):
    """Formata data para DDMMAA."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "000000"
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%d%m%y")
    # Tenta parsear string
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(valor).strip(), fmt).strftime("%d%m%y")
        except ValueError:
            continue
    return "000000"


def formata_cnpj_cpf(valor, tamanho=14):
    """Remove pontuação e retorna só dígitos, alinhado à direita com zeros."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "0" * tamanho
    s = ''.join(filter(str.isdigit, str(valor)))
    return s.zfill(tamanho)[-tamanho:]


def tipo_doc(valor):
    """Retorna 01=CPF ou 02=CNPJ baseado no tamanho do documento."""
    s = ''.join(filter(str.isdigit, str(valor))) if valor else ""
    return "01" if len(s) <= 11 else "02"


def especie_titulo(tipo):
    """Mapeia TIPO_RECEBIVEL para código de espécie."""
    mapa = {
        "DUPLICATA":         "01",
        "NP":                "02",
        "NOTA PROMISSORIA":  "02",
        "NOTA PROMISSORIA FISICA": "06",
        "DUPLICATA SERVICO": "14",
        "DUPLICATA DE SERVICO FISICA": "14",
        "CHEQUE":            "51",
        "CONTRATO":          "60",
        "CONTRATO FISICO":   "61",
        "CONFISSAO DE DIVIDA": "62",
        "FATURA CARTAO":     "65",
        "FATURA DE CARTAO CREDITO": "65",
    }



    
    
    if tipo is None or (isinstance(tipo, float) and pd.isna(tipo)):
        return "01"
    chave = str(tipo).upper().strip()
    chave = ''.join(c if c.isalnum() or c == ' ' else ' ' for c in chave)
    return mapa.get(chave, "01")


def valida_linha(linha):
    """Verifica que a linha tem exatamente 444 caracteres."""
    if len(linha) != LINHA_SIZE:
        raise ValueError(f"Linha com {len(linha)} chars (esperado {LINHA_SIZE}): '{linha}'")
    return linha


# ──────────────────────────────────────────────
# MONTAGEM DOS REGISTROS
# ──────────────────────────────────────────────

def monta_header(cfg, data_gravacao=None):
    if data_gravacao is None:
        data_gravacao = datetime.today().strftime("%d%m%y")

    linha = (
        "0"                                         # 1    pos 1      Identificação Registro
        + "1"                                       # 2    pos 2      Ident. Arquivo Remessa
        + alfa("Remessa", 7)                        # 3-9  pos 3-9    Literal Remessa
        + "01"                                      # 4    pos 10-11  Código Serviço
        + alfa("Cobranca", 15)                      # 5    pos 12-26  Literal Serviço
        + num(cfg["codigo_originador"], 20)         # 6    pos 27-46  Código Originador
        + alfa(cfg["nome_originador"], 30)          # 7    pos 47-76  Nome Originador
        + num(cfg["numero_banco"], 3)               # 8    pos 77-79  Número Banco
        + alfa(cfg["nome_banco"], 15)               # 9    pos 80-94  Nome Banco
        + data_gravacao                             # 10   pos 95-100 Data Gravação
        + alfa("", 8)                               # 11   pos 101-108 Branco
        + alfa(cfg["identificacao_sistema"], 2)     # 12   pos 109-110 Ident. Sistema
        + num(cfg["nr_sequencial_arquivo"], 7)      # 13   pos 111-117 Nº Seq. Arquivo
        + alfa("", 2)                               # 14   pos 118-119 Branco
        + num(cfg["valor_retencao"], 10)            # 15   pos 120-129 Valor Retenção
        + num(cfg["codigo_banco_dep"], 3)           # 16   pos 130-132 Código Banco
        + num(cfg["agencia_deposito"], 4)           # 17   pos 133-136 Agência Depósito
        + num(cfg["conta_corrente"], 14)            # 18   pos 137-150 Conta Corrente
        + alfa("", 288)                             # 19   pos 151-438 Branco
        + "000001"                                  # 20   pos 439-444 Nº Seq. Registro
    )
    return valida_linha(linha)


def monta_detalhe(row, cfg, seq):
    """Monta registro de detalhe (tipo 1) a partir de uma linha do DataFrame."""

    # Extrai e trata campos
    nome_sacado   = row.get("NOME_SACADO", "")
    doc_sacado    = row.get("DOC_SACADO", "")
    nome_cedente  = row.get("NOME_CEDENTE", "")
    doc_cedente   = row.get("DOC_CEDENTE", "")
    tipo_rec      = row.get("TIPO_RECEBIVEL", "")
    valor_pago    = row.get("Valor Pago", 0) or 0
    valor_nominal = row.get("VALOR_NOMINAL", 0) or 0
    valor_pres    = row.get("VALOR_PRESENTE", 0) or 0
    valor_aquis   = row.get("VALOR_AQUISICAO", 0) or 0
    dt_venc       = row.get("DATA_VENCIMENTO_AJUSTADA")
    dt_emis       = row.get("DATA_EMISSAO")
    dt_aquis      = row.get("DATA_AQUISICAO")
    nu_doc        = row.get("NU_DOCUMENTO", "")
    seu_numero    = row.get("SEU_NUMERO", "")

    # Número do termo de cessão = DATA_AQUISICAO (alfanumérico 19)
    nr_termo = alfa(str(formata_data(dt_aquis)), 19)

    # Nota fiscal = NU_DOCUMENTO (9 chars)
    nr_nf = alfa(str(nu_doc), 9)

    # Chave NF-e = 44 chars (preenche com brancos se não tiver)
    chave_nfe = alfa("", 44)

    # Cedente: 335-380 nome (46 chars) + 381-394 CNPJ (14 chars) = 60 chars
    nome_ced_fmt = alfa(nome_cedente, 46)
    cnpj_ced_fmt = formata_cnpj_cpf(doc_cedente, 14)
    cedente_campo = nome_ced_fmt + cnpj_ced_fmt  # 60 chars

    linha = (
        "1"                                             # 1   pos 1       Ident. Registro
        + alfa("", 19)                                  # 2   pos 2-20    Débito Automático C/C
        + cfg["coobrigacao"]                            # 3   pos 21-22   Coobrigação
        + "00"                                          # 4   pos 23-24   Característica Especial
        + "0000"                                        # 5   pos 25-28   Modalidade Operação
        + "00"                                          # 6   pos 29-30   Natureza Operação
        + "0000"                                        # 7   pos 31-34   Origem Recurso
        + alfa("", 2)                                   # 8   pos 35-36   Classe Risco
        + "0"                                           # 9   pos 37      Zeros
        + alfa(str(seu_numero), 25)                     # 10  pos 38-62   Nº Controle Participante
        + "000"                                         # 11  pos 63-65   Número Banco
        + "00000"                                       # 12  pos 66-70   Zeros
        + "00000000000"                                 # 13  pos 71-81   Ident. Título Banco
        + " "                                           # 14  pos 82      Dígito Nosso Número
        + num(valor_pago, 10, decimais=2)               # 15  pos 83-92   Valor Pago
        + " "                                           # 16  pos 93      Condição Emissão
        + " "                                           # 17  pos 94      Ident. Débito Aut.
        + formata_data(dt_venc)                         # 18  pos 95-100  Data Liquidação
        + alfa("", 4)                                   # 19  pos 101-104 Ident. Operação Banco
        + " "                                           # 20  pos 105     Indicador Rateio
        + "0"                                           # 21  pos 106     Endereçamento Débito Aut.
        + alfa("", 2)                                   # 22  pos 107-108 Branco
        + cfg["identificacao_ocorrencia"]               # 23  pos 109-110 Ident. Ocorrência
        + alfa(str(nu_doc), 10)                         # 24  pos 111-120 Nº Documento
        + formata_data(dt_venc)                         # 25  pos 121-126 Data Vencimento
        + num(valor_nominal, 13, decimais=2)            # 26  pos 127-139 Valor Título (Face)
        + "000"                                         # 27  pos 140-142 Banco Cobrança
        + "00000"                                       # 28  pos 143-147 Agência Depositária
        + especie_titulo(tipo_rec)                      # 29  pos 148-149 Espécie Título
        + " "                                           # 30  pos 150     Identificação
        + formata_data(dt_emis)                         # 31  pos 151-156 Data Emissão
        + "00"                                          # 32  pos 157-158 1ª Instrução
        + "0"                                           # 33  pos 159     2ª Instrução
        + tipo_doc(doc_cedente)                         # 34  pos 160-161 Tipo Pessoa Cedente
        + "000000000000"                                # 35  pos 162-173 Zeros (12 chars)
        + nr_termo                                      # 36  pos 174-192 Nº Termo Cessão (19)
        + num(valor_aquis, 13, decimais=2)              # 37  pos 193-205 Valor Presente Parcela
        + num(0, 13, decimais=2)                        # 38  pos 206-218 Valor Abatimento
        + tipo_doc(doc_sacado)                          # 39  pos 219-220 Tipo Inscrição Sacado
        + formata_cnpj_cpf(doc_sacado, 14)              # 40  pos 221-234 Nº Inscrição Sacado
        + alfa(nome_sacado, 40)                         # 41  pos 235-274 Nome Sacado
        + alfa("", 40)                                  # 42  pos 275-314 Endereço Sacado
        + nr_nf                                         # 43  pos 315-323 Nº NF Duplicata
        + alfa("", 3)                                   # 44  pos 324-326 Série NF
        + "00000000"                                    # 45  pos 327-334 CEP
        + cedente_campo                                 # 46  pos 335-394 Cedente (60)
        + chave_nfe                                     # 47  pos 395-438 Chave NF-e (44)
        + num(seq, 6)                                   # 48  pos 439-444 Nº Seq. Registro
    )

    # Ajuste: pos 162-173 = 12 chars de zeros (campo 35 é 162-173, tam=12 no spec original)
    # Verificação de tamanho
    if len(linha) != LINHA_SIZE:
        raise ValueError(
            f"Detalhe seq {seq} com {len(linha)} chars (esperado {LINHA_SIZE}).\n"
            f"Revise os campos. Linha:\n{linha}"
        )

    return linha


def monta_trailer(seq_total):
    linha = (
        "9"                     # 1   pos 1       Ident. Registro
        + alfa("", 437)         # 2   pos 2-438   Branco
        + num(seq_total, 6)     # 3   pos 439-444 Nº Seq. Último Registro
    )
    return valida_linha(linha)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def converter(caminho_excel, caminho_saida=None, cfg=None):
    if cfg is None:
        cfg = CONFIG

    # Lê o Excel
    df = pd.read_excel(caminho_excel, dtype=str)
    df.columns = df.columns.str.strip()

    # Colunas esperadas
    colunas_esperadas = [
        "NOME_CEDENTE", "DOC_CEDENTE", "NOME_SACADO", "DOC_SACADO",
        "TIPO_RECEBIVEL", "Valor Pago", "VALOR_NOMINAL", "VALOR_PRESENTE",
        "VALOR_AQUISICAO", "DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO",
        "DATA_AQUISICAO", "NU_DOCUMENTO", "SEU_NUMERO",
    ]
    faltando = [c for c in colunas_esperadas if c not in df.columns]
    if faltando:
        print(f"⚠️  Colunas não encontradas no Excel: {faltando}")

    hoje = datetime.today().strftime("%d%m%y")
    linhas = []

    # Header
    linhas.append(monta_header(cfg, data_gravacao=hoje))

    erros = []
    for i, row in df.iterrows():
        seq = i + 2  # header é seq 1
        try:
            linha = monta_detalhe(row.to_dict(), cfg, seq)
            linhas.append(linha)
        except Exception as e:
            erros.append(f"Linha {i+2} (Excel linha {i+2}): {e}")

    # Trailer
    seq_total = len(linhas) + 1
    linhas.append(monta_trailer(seq_total))

    # Nome de saída automático se não informado
    if caminho_saida is None:
        base = os.path.splitext(caminho_excel)[0]
        caminho_saida = base + ".REM"

    with open(caminho_saida, "w", encoding="ascii", errors="replace") as f:
        f.write("\r\n".join(linhas) + "\r\n")

    print(f"✅ Arquivo gerado: {caminho_saida}")
    print(f"   Registros de detalhe: {len(linhas) - 2}")
    if erros:
        print(f"\n⚠️  {len(erros)} erro(s) encontrado(s):")
        for e in erros:
            print(f"   {e}")

    return caminho_saida


# ──────────────────────────────────────────────
# USO VIA LINHA DE COMANDO
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python excel_to_cnab444.py <arquivo.xlsx> [saida.REM]")
        print("")
        print("Exemplo:")
        print("  python excel_to_cnab444.py remessa.xlsx CB050501.REM")
        sys.exit(1)

    entrada = sys.argv[1]
    saida   = sys.argv[2] if len(sys.argv) > 2 else None

    converter(entrada, saida)
