import streamlit as st
import pandas as pd
import plotly.express as px


from zipfile import ZipFile

from io import BytesIO

from src.utils_visuals import plot_pdd_horizontal
from src.classes.Formater import Formater as fmt  
from src.data_loader import ler_zip, ler_csv
from src.classes.analise_pdd import categorizar_prazo,percentual_pdd,ordenar_pdd,processar_pdd,criar_dataframe_pdd,CONFIG_PDD


pct = fmt.formatar_percentual
hmz = fmt.formatar_pl_humano
nmr = fmt.formatar_numero
nmrd = fmt.formatar_numero_decimal

st.title("📉 Análise PDD")

# CONFIGURAÇÕES DE PDD
col1, col2 = st.columns(2)

arquivo_estoque = col1.file_uploader("Arquivo de Estoque (ZIP ou CSV)", type=["zip", "csv"])

opcoes_prefixos = sorted(list(set(f.split('-')[0] for f in CONFIG_PDD.keys())))
tipo_pdd = col2.selectbox("Tipo de PDD", opcoes_prefixos)

fundos = [f for f in CONFIG_PDD.keys() if f.startswith(tipo_pdd)]
fundo_selecionado = col2.selectbox("Fundo", fundos)

faixas = CONFIG_PDD[fundo_selecionado]["faixas"]

usar_vagao = st.toggle("Agrupar por sacado (modo vagão)", value=True)
filtrar_wop_toggle = st.toggle("Filtrar WOP", value=True)

if not arquivo_estoque:
    st.stop()

if st.button("🚀 Processar"):
    with st.spinner("Processando..."):
        if arquivo_estoque.name.endswith(".zip"):
            df_estoque = ler_zip(arquivo_estoque)
        else:
            df_estoque = ler_csv(arquivo_estoque)
        resultado = processar_pdd(df_estoque, usar_vagao, faixas, filtrar_wop_toggle)
        df_pdd_processado = criar_dataframe_pdd(df_estoque) # Criando o dataframe
        
        # Salva tudo no session_state
        st.session_state["pdd_resultado"] = resultado
        st.session_state["df_pdd"] = df_pdd_processado 
        st.session_state["pdd_data_ref"] = df_estoque["DATA_REFERENCIA"].iloc[0]
        st.session_state["filtrar_wop"] = filtrar_wop_toggle

# Só segue se AMBOS existirem no estado da sessão
if "pdd_resultado" not in st.session_state or "df_pdd" not in st.session_state:
    st.stop()

# Recupera os dados
df = st.session_state["pdd_resultado"]
df_pdd = st.session_state["df_pdd"]
total = df[df["FAIXA_PDD"] == "Total"].iloc[0]

# Define colunas com proporção 1 para 3 (c2 terá 75% da largura)
c1, c2 = st.columns([1, 3])

df_perc = df[df["FAIXA_PDD"] != "Total"]
if st.session_state.get("filtrar_wop", True):
    df_perc = df_perc[df_perc['FAIXA_PDD'] != 'WOP']
with c1:
    st.write("Distribuição de faixas")
    # Removi um '%' extra que estava na sua string de formato para não repetir
    st.dataframe(
        df_perc[["FAIXA_PDD","% PDD"]].style.format({'% PDD': "{:.1%}"}),
        hide_index=True,
        use_container_width=True
    )

with c2:
    st.write("Detalhamento PDD")
    st.dataframe(
        df_pdd.style.format({
            'Carteira Atraso':nmr,
            'PDD s/ WO':nmr,
            'PDD / Carteira Atraso': "{:.0%}",
            '(WOP)':nmr,
            'Carteira VP':nmr,
            'PDD Total':nmr,
            'PDD / Carteira':'{:.0%}',
            },na_rep="-"),
        hide_index=True,
        use_container_width=True)

   # Criando o gráfico de barras horizontais (barh)
    plot_pdd_horizontal(df_perc,
                        x = "PDD POR FAIXA",
                        y="FAIXA_PDD")

    buffer = BytesIO()
    
    _,btn1,btn2 = st.columns([4,1,1])
    
    with btn1:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_pdd.to_excel(writer, index=False)
        st.download_button("📥 Excel", buffer.getvalue(), f"{fundo_selecionado}_resumo_pdd.xlsx", use_container_width=True)

    with btn2:
        csv = df_pdd.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV", csv, f"{fundo_selecionado}_resumo_pdd.csv", use_container_width=True)

st.caption(f"Data de referência: {st.session_state['pdd_data_ref']}")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Valor Nominal", f"{hmz(total['VALOR_NOMINAL'])}")
c2.metric("Valor Presente", f"{hmz(total['VALOR_PRESENTE'])}")
c3.metric("Valor Aquisição", f"{hmz(total['VALOR_AQUISICAO'])}")
c4.metric("PDD por Faixa", f"{hmz(total['PDD POR FAIXA'])}")

# Tabela
st.dataframe(
    df.style.format({
        "VALOR_AQUISICAO": nmrd,
        "VALOR_NOMINAL": nmrd,
        "VALOR_PRESENTE": nmrd,
        "VALOR_PDD": nmrd,
        "PDD POR FAIXA": nmrd,
        "% PDD": "{:.0%}",
    }, na_rep="-"),
    use_container_width=True,
    hide_index=True,
)

# Downloads

    
    # Downloads
_, btn1, btn2 = st.columns([8, 1.5, 1.5])  

with btn1:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name='PDD')

    data_xlsx = buffer.getvalue()
    
    st.download_button(
        label="📥 Excel",
        data=data_xlsx,
        file_name=f"{fundo_selecionado}_pdd_consolidado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with btn2:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 CSV",
        data=csv,
        file_name=f"{fundo_selecionado}_pdd_consolidado.csv",
        mime="text/csv",
        use_container_width=True
    )
