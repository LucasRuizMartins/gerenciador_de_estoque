import streamlit as st
import pandas as pd
import numpy as np
from zipfile import ZipFile
from io import BytesIO

st.title("📊 Análise PDD")

# ══════════════════════════════════════════════════════
# CONFIGURAÇÕES DE PDD
# ══════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════
# FUNÇÕES
# ══════════════════════════════════════════════════════

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


# def ordenar_pdd(df, faixas):
#     ordem = ["A vencer"] + [f[0] for f in faixas]
#     df["FAIXA_PDD"] = pd.Categorical(df["FAIXA_PDD"], categories=ordem, ordered=True)
#     return df.sort_values("FAIXA_PDD").reset_index(drop=True)
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

def ler_zip(file):
    dfs = []
    with ZipFile(file) as z:
        for name in z.namelist():
            if name.endswith(".csv"):
                with z.open(name) as f:
                    dfs.append(pd.read_csv(
                        f,
                        encoding="ISO-8859-1",
                        delimiter=";",
                        decimal=",",
                        thousands=".",
                        on_bad_lines="skip",
                        low_memory=False
                    ))
    return pd.concat(dfs, ignore_index=True)


def processar_pdd(df_estoque, usar_vagao, faixas):
    COLUNAS = [
        "DOC_SACADO", "SEU_NUMERO", "SITUACAO_RECEBIVEL",
        "NU_DOCUMENTO", "VALOR_PDD", "PRAZO_ATUAL",
        "VALOR_AQUISICAO", "VALOR_NOMINAL", "VALOR_PRESENTE", "DATA_REFERENCIA"
    ]

    df = df_estoque[[c for c in COLUNAS if c in df_estoque.columns]].copy()

    # Garantir tipos
    df["PRAZO_ATUAL"] = pd.to_numeric(df["PRAZO_ATUAL"], errors="coerce")
    df["VALOR_PRESENTE"] = pd.to_numeric(df["VALOR_PRESENTE"], errors="coerce")

    # Classificação inicial
    df["FAIXA_PDD"] = df["PRAZO_ATUAL"].apply(lambda x: categorizar_prazo(x, faixas))

    # Modo vagão (igual lógica antiga)
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

    # DEBUG (pode comentar depois)
    st.write("Distribuição de faixas antes filtro:")
    st.write(df["FAIXA_PDD"].value_counts(dropna=False))

    # Remover A vencer (CORRETO)
    #df = df[df["FAIXA_PDD"] != "A vencer"]

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

# ══════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════

col1, col2 = st.columns(2)

zip_file = col1.file_uploader("📦 ZIP do Estoque", type=["zip"])

opcoes_prefixos = sorted(list(set(f.split('-')[0] for f in CONFIG_PDD.keys())))
tipo_pdd = col2.selectbox("Tipo de PDD", opcoes_prefixos)

fundos = [f for f in CONFIG_PDD.keys() if f.startswith(tipo_pdd)]
fundo_selecionado = col2.selectbox("Fundo", fundos)

faixas = CONFIG_PDD[fundo_selecionado]["faixas"]

usar_vagao = st.toggle("Agrupar por sacado (modo vagão)", value=True)

if not zip_file:
    st.stop()

if st.button("🚀 Processar"):
    with st.spinner("Processando..."):
        df_estoque = ler_zip(zip_file)
        resultado = processar_pdd(df_estoque, usar_vagao, faixas)

        st.session_state["pdd_resultado"] = resultado
        st.session_state["pdd_data_ref"] = df_estoque["DATA_REFERENCIA"].iloc[0]

if "pdd_resultado" not in st.session_state:
    st.stop()

df = st.session_state["pdd_resultado"]
total = df[df["FAIXA_PDD"] == "Total"].iloc[0]

st.caption(f"Data de referência: {st.session_state['pdd_data_ref']}")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor Nominal", f"R$ {total['VALOR_NOMINAL']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c2.metric("Valor Presente", f"R$ {total['VALOR_PRESENTE']:,.2f}")
c3.metric("Valor Aquisição", f"R$ {total['VALOR_AQUISICAO']:,.2f}")
c4.metric("PDD por Faixa", f"R$ {total['PDD POR FAIXA']:,.2f}")

# Tabela
st.dataframe(
    df.style.format({
        "VALOR_AQUISICAO": "R$ {:,.2f}",
        "VALOR_NOMINAL": "R$ {:,.2f}",
        "VALOR_PRESENTE": "R$ {:,.2f}",
        "VALOR_PDD": "R$ {:,.2f}",
        "% PDD": "{:.0%}",
        "PDD POR FAIXA": "R$ {:,.2f}",
    }, na_rep="-"),
    use_container_width=True,
    hide_index=True,
)

# Downloads
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)

st.download_button("📥 Excel", buffer.getvalue(), "pdd.xlsx")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("📥 CSV", csv, "pdd.csv")