import pandas as pd
import numpy as np

CONFIG_PDD = {
    "APEX-MOOVPAY": {
        "faixas": [
            ("0~9", 0, -9, 0.055),
            ("10~22", -10, -22, 0.0265),
            ("23~38", -23, -38, 0.0617),
            ("39~53", -39, -53, 0.2588),
            ("54~64", -54, -64, 0.3358),
            ("65~75", -65, -75, 0.4238),
            ("76~86", -76, -86, 0.5142),
            ("87~101", -87, -101, 0.6281),
            ("102~116", -102, -116, 0.7604),
            ("117~131", -117, -131, 0.8757),
            ("132~145", -132, -145, 0.9932),
            ("+145", None, -146, 1.0),
        ]
    },
    "QI-MOOVPAY": {
        "faixas": [
            ("1~5", 0, -5, 0.0),
            ("6~30", -6, -30, 0.0114),
            ("31~60", -31, -60, 0.1354),
            ("61~90", -61, -90, 0.3229),
            ("91~120", -91, -120, 0.6559),
            ("+120", None, -121, 1.0),
        ]
    },
    "APEX-RESIDENCE": {
    "faixas": [
        ("1~13", -1, -13, 0.038235),
        ("14~42", -14, -42, 0.123529),
        ("43~87", -43, -87, 0.255882),
        ("88~125", -88, -125, 0.367647),
        ("126~157", -126, -157, 0.461765),
        ("158~188", -158, -188, 0.552941),
        ("189~217", -189, -217, 0.638335),
        ("218~248", -218, -248, 0.729412),
        ("249~278", -249, -278, 0.817647),
        ("279~308", -279, -308, 0.905882),
        ("309~339", -309, -339, 0.997059),
        ("+340", None, -340, 1.0),
    ]
}
}


def categorizar_prazo(prazo, faixas):
    if pd.isna(prazo):
        return "A vencer"
    for nome, limite_sup, limite_inf, _ in faixas:
        if limite_sup is not None:
            if prazo <= limite_sup and prazo >= limite_inf:
                return nome
        else:
            if prazo < limite_inf:
                return nome
    return "A vencer"


def percentual_pdd(faixa, faixas):
    return float(next((pct for nome, *_, pct in faixas if nome == faixa), 0.0))


def ordenar_pdd(df, faixas):
    ordem = ["A vencer"] + [f[0] for f in faixas]

    # garante que só usamos faixas existentes + A vencer
    ordem_existente = [o for o in ordem if o in df["FAIXA_PDD"].unique()]

    df["FAIXA_PDD"] = pd.Categorical(
        df["FAIXA_PDD"],
        categories=ordem_existente,
        ordered=True
    )

    return df.sort_values("FAIXA_PDD").reset_index(drop=True)


def processar_pdd(df_estoque, usar_vagao, faixas, filtrar_wop=True):
    COLUNAS = [
        "DOC_SACADO", "SEU_NUMERO", "SITUACAO_RECEBIVEL",
        "NU_DOCUMENTO", "VALOR_PDD", "PRAZO_ATUAL",
        "VALOR_AQUISICAO", "VALOR_NOMINAL", "VALOR_PRESENTE", "DATA_REFERENCIA"
    ]
    if filtrar_wop and "FAIXA_PDD" in df_estoque.columns:
        df_estoque = df_estoque[df_estoque['FAIXA_PDD'] !='WOP']
    df = df_estoque[[c for c in COLUNAS if c in df_estoque.columns]].copy()

    # Garantir tipos
    df["PRAZO_ATUAL"] = pd.to_numeric(df["PRAZO_ATUAL"], errors="coerce")
    df["VALOR_PRESENTE"] = pd.to_numeric(df["VALOR_PRESENTE"], errors="coerce")
    df["FAIXA_PDD"] = df["PRAZO_ATUAL"].apply(lambda x: categorizar_prazo(x, faixas))

    if usar_vagao:
        df = df.groupby("DOC_SACADO").agg(
            VALOR_AQUISICAO=("VALOR_AQUISICAO", "sum"),
            VALOR_NOMINAL=("VALOR_NOMINAL", "sum"),
            VALOR_PRESENTE=("VALOR_PRESENTE", "sum"),
            PRAZO_ATUAL=("PRAZO_ATUAL", "min"),
            VALOR_PDD=("VALOR_PDD", "sum"),
            DATA_REFERENCIA=("DATA_REFERENCIA", "first"),
        ).reset_index()

        df["FAIXA_PDD"] = df["PRAZO_ATUAL"].apply(lambda x: categorizar_prazo(x, faixas))

    # Agrupamento final
    df_final = df.groupby("FAIXA_PDD").agg(
        VALOR_AQUISICAO=("VALOR_AQUISICAO", "sum"),
        VALOR_NOMINAL=("VALOR_NOMINAL", "sum"),
        VALOR_PRESENTE=("VALOR_PRESENTE", "sum"),
        VALOR_PDD=("VALOR_PDD", "sum"),
        DATA_REFERENCIA=("DATA_REFERENCIA", "first")
    ).reset_index()

    # Percentual
    df_final["% PDD"] = df_final["FAIXA_PDD"].apply(lambda x: percentual_pdd(x, faixas))

    # Cálculo
    df_final["PDD POR FAIXA"] = df_final["VALOR_PRESENTE"] * df_final["% PDD"]

    # Linha total
    total = {
        "FAIXA_PDD": "Total",
        "VALOR_AQUISICAO": df_final["VALOR_AQUISICAO"].sum(),
        "VALOR_NOMINAL": df_final["VALOR_NOMINAL"].sum(),
        "VALOR_PRESENTE": df_final["VALOR_PRESENTE"].sum(),
        "VALOR_PDD": df_final["VALOR_PDD"].sum(),
        "% PDD": np.nan,
        "PDD POR FAIXA": df_final["PDD POR FAIXA"].sum(),
        "DATA_REFERENCIA": df_final["DATA_REFERENCIA"].iloc[0],
    }

    df_final = pd.concat([df_final, pd.DataFrame([total])], ignore_index=True)

    # 🔥 AQUI entra a lógica de ordenação correta
    df_total = df_final[df_final["FAIXA_PDD"] == "Total"]
    df_sem_total = df_final[df_final["FAIXA_PDD"] != "Total"]

    df_sem_total = ordenar_pdd(df_sem_total, faixas)

    df_final = pd.concat([df_sem_total, df_total], ignore_index=True)

    return df_final





def criar_dataframe_pdd(df):
    atraso_vp = df[df['SITUACAO_RECEBIVEL'] == 'Vencido']['VALOR_PRESENTE'].sum()
    pdd_sem_wop = df[df['FAIXA_PDD'] != 'WOP']['VALOR_PDD'].sum()
    pdd_wop = df[df['FAIXA_PDD'] == 'WOP']['VALOR_PDD'].sum()
    valor_presente = df['VALOR_PRESENTE'].sum()
    total_pdd = df['VALOR_PDD'].sum()
    
    df_pdd = pd.DataFrame({
    'Carteira Atraso': [atraso_vp],
    'PDD s/ WO': [pdd_sem_wop],
    'PDD / Carteira Atraso': [pdd_sem_wop / atraso_vp if atraso_vp != 0 else 0],
    '(WOP)': [pdd_wop],
    'Carteira VP': [valor_presente],
    'PDD Total': [total_pdd],
    'PDD / Carteira': [total_pdd / valor_presente if valor_presente != 0 else 0]
    })
    return df_pdd