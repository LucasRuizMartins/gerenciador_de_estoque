import streamlit as st
import pandas as pd
import os
import io
from src.analise_estoque import AnaliseEstoque  

 

st.title("📊 Análise de Estoque de Recebíveis")

# ── Seleção de arquivo por Upload ──────────────────────────────
arquivo_selecionado = st.file_uploader(
    "Faça o upload do arquivo de estoque", 
    type=['zip', 'csv', 'xlsx', 'xls'],
    help="Arraste o arquivo diretamente da sua pasta do SharePoint para cá."
)

if arquivo_selecionado is not None:
    st.success(f"Arquivo '{arquivo_selecionado.name}' carregado com sucesso!")
else:
    st.info("Por favor, faça o upload de um arquivo para iniciar a análise.")
    st.stop()


# ── Processamento ──────────────────────────────────────────────
# Usamos o arquivo_selecionado diretamente (o objeto de upload)
if st.button("🚀 Processar"):
    with st.spinner("Processando... Isso pode levar alguns minutos para arquivos grandes."):
        try:
            # Garanta que sua classe AnaliseEstoque aceite o objeto de arquivo no __init__
            analise = AnaliseEstoque(arquivo_selecionado)
            st.session_state["analise"] = analise
            st.success("✅ Processamento concluído!")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")


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
col3.metric("Total Sacados",  f"{analise.total_sacados:,}")
col4.metric("Total Cedentes", f"{analise.total_cedentes:,}")

# ── Quantidades ────────────────────────────────────────────────
st.subheader("📜 Títulos")
col1, col2, col3 = st.columns(3)
col1.metric("Total Títulos",    f"{m.qtd_aquisicao:,}")
col2.metric("Títulos A Vencer", f"{m.qtd_a_vencer:,}")
col3.metric("Títulos Vencidos", f"{m.qtd_vencido:,}")

# ── Mês atual ──────────────────────────────────────────────────
st.subheader("📅 Aquisições no Mês")
col1, col2 = st.columns(2)
col1.metric("Valor Aquisição no Mês", fmt(mm.valor_aquisicao_mes))
col2.metric("Qtd Aquisição no Mês",   f"{mm.qtd_aquisicao_mes:,}")

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
col2.metric("Mediana (A Vencer)", fmt(m.mediana_a_vencer))
col3.metric("Mediana (Vencido)",  fmt(m.mediana_vencido))

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
tipo_sel = st.selectbox("Selecione o tipo:", tipos) if tipos else None

if tipo_sel:
    mg = analise.metricas_globais_por_tipo[tipo_sel]
    mv_t = analise.metricas_vencimento_por_tipo[tipo_sel]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Presente", fmt(mg.valor_presente))
    col2.metric("A Vencer",       fmt(mg.valor_a_vencer))
    col3.metric("Vencido",        fmt(mg.valor_vencido))
    col4.metric("PDD",            fmt(mg.valor_pdd))

    col1, col2, col3 = st.columns(3)
    col1.metric("Prazo Médio",          f"{mg.prazo_medio:.1f} dias")
    col2.metric("Mediana V.A",   fmt(mg.mediana_valor_aquisicao))
    col3.metric("Mediana Taxa Cessão",  pct(mg.mediana_taxa_cessao/100))

    df_faixas_tipo = pd.DataFrame({
        "Faixa (dias)": faixas_label,
        "A Vencer (VP)": [fmt(getattr(mv_t, f"a_vencer_{a}", 0))     for a in faixas_attr],
        "Vencido (VP)":  [fmt(getattr(mv_t, f"vencido_{a}", 0))      for a in faixas_attr],
        "PDD A Vencer":  [fmt(getattr(mv_t, f"pdd_a_vencer_{a}", 0)) for a in faixas_attr],
        "PDD Vencido":   [fmt(getattr(mv_t, f"pdd_vencido_{a}", 0))  for a in faixas_attr],
    })
    st.dataframe(df_faixas_tipo, use_container_width=True, hide_index=True)

# ── Cedentes e Recebíveis ──────────────────────────────────────
st.subheader("🏢 Cedentes")
df_cedentes = analise.obter_cedentes_agrupados()
df_cedentes['VALOR_PRESENTE'] = df_cedentes['VALOR_PRESENTE'].apply(hmz)
#df_cedentes['VALOR_PRESENTE'] = df_cedentes['VALOR_PRESENTE'].apply(pct)

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
nome_base = arquivo_selecionado.name.split('.')[0]
nome_arquivo = f"relatorio_{nome_base}_{data_atual}.xlsx"

if st.button("📥 Gerar arquivo para download"):
    with st.spinner("Gerando arquivo..."):
        try:
            if "analise" in st.session_state:
                buffer = io.BytesIO()
                analise.exportar_para_excel(buffer)
                buffer.seek(0)

                st.download_button(
                    "⬇️ Baixar Excel",
                    buffer,
                    file_name=nome_arquivo
                )
        except Exception as e:
            st.error(f"Erro ao gerar arquivo: {e}")