import streamlit as st
import pandas as pd
import os
import io
from src.classes.analise_estoque import AnaliseEstoque  

from src.components import selector

st.title("📊 Análise de Estoque de Recebíveis")

selector.componente_upload_processamento("Faça o upload do arquivo de estoque",
                                         AnaliseEstoque,
                                         'analise')


# ── Exibição das métricas ──────────────────────────────────────
if "analise" not in st.session_state:
    st.stop()

analise: AnaliseEstoque = st.session_state["analise"]
m  = analise.metricas_globais
mm = analise.metricas_mensais
mv = analise.metricas_vencimento

fmt = AnaliseEstoque.formatar_moeda
pct = AnaliseEstoque.formatar_percentual
hmz = AnaliseEstoque.formatar_pl_humano
nmr = AnaliseEstoque.formatar_numero

# ── Header ────────────────────────────────────────────────────
st.header(f"🏦 {m.nome_fundo}")
st.caption(f"Data de referência: {mm.data_ref.strftime('%d/%m/%Y')}")

# ── KPIs principais ────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Valor Presente Total",   fmt(m.valor_presente))
col2.metric("Valor Nominal Total",    fmt(m.valor_nominal))
col3.metric("Valor Aquisição Total",  fmt(m.valor_aquisicao))
col4.metric("PDD",                    fmt(m.valor_pdd))

col1, col2, col3, col4 = st.columns(4)
col1.metric("A Vencer",       fmt(m.valor_a_vencer))
col2.metric("Vencido",        fmt(m.valor_vencido))
col3.metric("Total Sacados",  f"{nmr(analise.total_sacados)}")
col4.metric("Total Cedentes", f"{nmr(analise.total_cedentes)}")

# ── Quantidades ────────────────────────────────────────────────
st.subheader("📜 Títulos")
col1, col2, col3 = st.columns(3)
col1.metric("Total Títulos",    f"{nmr(m.qtd_aquisicao)}")
col2.metric("Títulos A Vencer", f"{nmr(m.qtd_a_vencer)}")
col3.metric("Títulos Vencidos", f"{nmr(m.qtd_vencido)}")

# ── Mês atual ──────────────────────────────────────────────────
st.subheader("📅 Aquisições no Mês")
col1, col2 = st.columns(2)
col1.metric("Valor Aquisição no Mês", fmt(mm.valor_aquisicao_mes))
col2.metric("Qtd Aquisição no Mês",   f"{nmr(mm.qtd_aquisicao_mes)}")

# ── Última quinzena ────────────────────────────────────────────
st.subheader("🕐 Última Quinzena")
col1, col2, col3 = st.columns(3)
col1.metric("VP Total",      fmt(m.ultima_quinzena_valor_presente))
col2.metric("VP A Vencer",   fmt(m.ultima_quinzena_valor_a_vencer))
col3.metric("VP Vencido",    fmt(m.ultima_quinzena_valor_vencido))

col1, col2, col3 = st.columns(3)
col1.metric("Aquisição Total",    fmt(m.ultima_quinzena_valor_aquisicao))
col2.metric("Aquisição A Vencer", fmt(m.ultima_quinzena_valor_aquisicao_a_vencer))
col3.metric("Aquisição Vencido",  fmt(m.ultima_quinzena_valor_aquisicao_vencido))

# ── Tickets médios ─────────────────────────────────────────────
st.subheader("📊 Ticket Médio")

with st.expander("Ver tickets médios detalhados"):
    df_tickets = pd.DataFrame({
        "Métrica": [
            "Ticket Presente Total", "Ticket Presente A Vencer", "Ticket Presente Vencido",
            "Ticket Aquisição Total", "Ticket Aquisição A Vencer", "Ticket Aquisição Vencido",
            "Ticket Nominal Total", "Ticket Nominal A Vencer", "Ticket Nominal Vencido",
        ],
        "Total": [
            fmt(m.ticket_medio_presente_total), fmt(m.ticket_medio_presente_a_vencer), fmt(m.ticket_medio_presente_vencido),
            fmt(m.ticket_medio_aquisicao_total), fmt(m.ticket_medio_aquisicao_a_vencer), fmt(m.ticket_medio_aquisicao_vencido),
            fmt(m.ticket_medio_nominal_total), fmt(m.ticket_medio_nominal_a_vencer), fmt(m.ticket_medio_nominal_vencido),
        ],
        "Última Quinzena": [
            fmt(m.ultima_quinzena_ticket_medio_presente_total), fmt(m.ultima_quinzena_ticket_medio_presente_a_vencer), fmt(m.ultima_quinzena_ticket_medio_presente_vencido),
            fmt(m.ultima_quinzena_ticket_medio_aquisicao_total), fmt(m.ultima_quinzena_ticket_medio_aquisicao_a_vencer), fmt(m.ultima_quinzena_ticket_medio_aquisicao_vencido),
            fmt(m.ultima_quinzena_ticket_medio_nominal_total), fmt(m.ultima_quinzena_ticket_medio_nominal_a_vencer), fmt(m.ultima_quinzena_ticket_medio_nominal_vencido),
        ],
    })
    st.dataframe(df_tickets, use_container_width=True, hide_index=True)

# ── Prazos e Taxas ─────────────────────────────────────────────
st.subheader("📈 Prazos Médios & Taxas")
col1, col2, col3 = st.columns(3)
col1.metric("Prazo Médio Total",   f"{m.prazo_medio:.1f} dias")
col2.metric("Prazo Médio A Vencer", f"{m.prazo_medio_a_vencer:.1f} dias")
col3.metric("Prazo Médio Vencido", f"{m.prazo_medio_vencido:.1f} dias")

col1, col2, col3 = st.columns(3)
col1.metric("Mediana Taxa (Total)",    pct(m.mediana_taxa_media))
col2.metric("Mediana (A Vencer)", pct(m.mediana_a_vencer))
col3.metric("Mediana (Vencido)",  pct(m.mediana_vencido))

# ── Faixas de Vencimento ───────────────────────────────────────
st.subheader("📆 Faixas de Vencimento")

faixas_label = ["0-15", "16-30", "31-60", "61-90", "91-120", "121-150", "151-180", "181-360", "+360"]
faixas_attr  = ["0_15", "16_30", "31_60", "61_90", "91_120", "121_150", "151_180", "181_360", "acima_360"]

df_faixas = pd.DataFrame({
    "Faixa (dias)": faixas_label,
    "A Vencer (VP)":   [fmt(getattr(mv, f"a_vencer_{a}", 0))  for a in faixas_attr],
    "Vencido (VP)":    [fmt(getattr(mv, f"vencido_{a}", 0))   for a in faixas_attr],
    "PDD A Vencer":    [fmt(getattr(mv, f"pdd_a_vencer_{a}", 0)) for a in faixas_attr],
    "PDD Vencido":     [fmt(getattr(mv, f"pdd_vencido_{a}", 0))  for a in faixas_attr],
})
st.dataframe(df_faixas, use_container_width=True, hide_index=True)

# ── Por Tipo de Recebível ──────────────────────────────────────
st.subheader("🗂️ Por Tipo de Recebível")

tipos = sorted(analise.metricas_globais_por_tipo.keys())
opcoes = ["Todos"] + tipos

tipo_sel = st.selectbox("Selecione o tipo:", opcoes) if tipos else None

# Funções auxiliares
def soma_metricas(attr):
    return sum(getattr(mg, attr, 0) for mg in analise.metricas_globais_por_tipo.values())

def soma_faixa(attr):
    return sum(getattr(mv, attr, 0) for mv in analise.metricas_vencimento_por_tipo.values())


if tipo_sel:

#----------------Total
    if tipo_sel == "Todos":

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Valor Presente", fmt(soma_metricas("valor_presente")))
        col2.metric("A Vencer",       fmt(soma_metricas("valor_a_vencer")))
        col3.metric("Vencido",        fmt(soma_metricas("valor_vencido")))
        col4.metric("PDD",            fmt(soma_metricas("valor_pdd")))

        #  média simples (se quiser te faço ponderada depois)
        import numpy as np
        prazo_medio = np.mean([
            mg.prazo_medio for mg in analise.metricas_globais_por_tipo.values()
        ])

        col1, col2, col3 = st.columns(3)
        col1.metric("Prazo Médio", f"{prazo_medio:.1f} dias")
        col2.metric("Mediana V.A", pct(soma_metricas("mediana_valor_aquisicao")))
        col3.metric("Mediana Taxa Cessão", pct(soma_metricas("mediana_taxa_cessao")/100))

        df_faixas_tipo = pd.DataFrame({
            "Faixa (dias)": faixas_label,
            "A Vencer (VP)": [fmt(soma_faixa(f"a_vencer_{a}"))     for a in faixas_attr],
            "Vencido (VP)":  [fmt(soma_faixa(f"vencido_{a}"))      for a in faixas_attr],
            "PDD A Vencer":  [fmt(soma_faixa(f"pdd_a_vencer_{a}")) for a in faixas_attr],
            "PDD Vencido":   [fmt(soma_faixa(f"pdd_vencido_{a}"))  for a in faixas_attr],
        })

        st.dataframe(df_faixas_tipo, width='stretch', hide_index=True)
#----------------Filtro
    else:
        mg = analise.metricas_globais_por_tipo[tipo_sel]
        mv_t = analise.metricas_vencimento_por_tipo[tipo_sel]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Valor Presente", fmt(mg.valor_presente))
        col2.metric("A Vencer",       fmt(mg.valor_a_vencer))
        col3.metric("Vencido",        fmt(mg.valor_vencido))
        col4.metric("PDD",            fmt(mg.valor_pdd))

        col1, col2, col3 = st.columns(3)
        col1.metric("Prazo Médio", f"{mg.prazo_medio:.1f} dias")
        col2.metric("Mediana V.A", pct(mg.mediana_valor_aquisicao))
        col3.metric("Mediana Taxa Cessão", pct(mg.mediana_taxa_cessao/100))

        df_faixas_tipo = pd.DataFrame({
            "Faixa (dias)": faixas_label,
            "A Vencer (VP)": [fmt(getattr(mv_t, f"a_vencer_{a}", 0))     for a in faixas_attr],
            "Vencido (VP)":  [fmt(getattr(mv_t, f"vencido_{a}", 0))      for a in faixas_attr],
            "PDD A Vencer":  [fmt(getattr(mv_t, f"pdd_a_vencer_{a}", 0)) for a in faixas_attr],
            "PDD Vencido":   [fmt(getattr(mv_t, f"pdd_vencido_{a}", 0))  for a in faixas_attr],
        })

        st.dataframe(df_faixas_tipo, width='stretch', hide_index=True)
        


# ── Cedentes e Recebíveis ──────────────────────────────────────
st.subheader("🏢 Cedentes")
df_cedentes = analise.obter_cedentes_agrupados()
df_cedentes['VALOR_PRESENTE'] = df_cedentes['VALOR_PRESENTE'].apply(hmz)
 
st.dataframe(df_cedentes, use_container_width=True, hide_index=True)

st.subheader("📋 Recebíveis por Tipo")
df_recebiveis = analise.obter_recebiveis_agrupados()

colunas_numericas = ['VALOR_PRESENTE','VALOR_NOMINAL','VALOR_AQUISICAO']

df_recebiveis['VALOR_PRESENTE'] = df_recebiveis['VALOR_PRESENTE'].apply(hmz)
df_recebiveis['VALOR_NOMINAL'] = df_recebiveis['VALOR_NOMINAL'].apply(hmz)
df_recebiveis['VALOR_AQUISICAO'] = df_recebiveis['VALOR_AQUISICAO'].apply(hmz)

st.dataframe(df_recebiveis, use_container_width=True, hide_index=True)

# ── Exportar Excel ─────────────────────────────────────────────
st.subheader("💾 Exportar")
from datetime import datetime

data_atual = datetime.now().strftime("%d_%m_%Y")
nome_base = m.nome_fundo.split()[0] #arquivo_selecionado.name.split('.')[0]
nome_arquivo = f"relatorio_{nome_base}_{data_atual}.xlsx"

buffer = io.BytesIO()
analise.exportar_para_excel(buffer)
buffer.seek(0)


if st.button("📥 Gerar arquivo"):
    buffer = io.BytesIO()
    sucesso = analise.exportar_para_excel(buffer)

    if sucesso:
        buffer.seek(0)

        st.download_button(
            "⬇️ Baixar Excel",
            data=buffer.getvalue(),
            file_name=nome_arquivo,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Erro ao gerar arquivo")