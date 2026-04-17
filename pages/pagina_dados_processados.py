import streamlit as st
import pandas as pd
import os
from src.AnaliseEstoque import AnaliseEstoque  

# ── Configuração do caminho base ───────────────────────────────
# 1. Tenta identificar se está no Windows (Seu PC) ou Linux (Streamlit Cloud)
if "USERPROFILE" in os.environ:
    user_profile = os.environ["USERPROFILE"]
    path_base = os.path.join(user_profile, 'Carmel Capital', 'Arquivos - Documentos',
                             '00 - CARMEL ASSET', '01 - OPERACIONAL', 'TECNOLOGIA', 'BASE_ESTOQUE_ANALISE')
else:
    path_base = os.path.join(os.getcwd(), 'BASE_ESTOQUE_ANALISE')
 
if not os.path.exists(path_base):
    st.error(f"⚠️ Pasta de dados não encontrada: {path_base}")
    st.info("Se estiver no servidor, certifique-se de que os arquivos foram enviados ao repositório.")
else:
    st.success("✅ Conectado à base de dados.")

st.title("📊 Análise de Estoque de Recebíveis")


# ── Seleção de arquivo ─────────────────────────────────────────
if not os.path.exists(path_base):
    st.error(f"Diretório não encontrado: {path_base}")
    st.stop()

arquivos = [f for f in os.listdir(path_base)
            if os.path.isfile(os.path.join(path_base, f))
            and f.endswith(('.zip', '.csv', '.xlsx', '.xls'))]

if not arquivos:
    st.warning("Nenhum arquivo encontrado na pasta.")
    st.stop()

arquivo_selecionado = st.selectbox("Selecione o arquivo:", arquivos)
file_path = os.path.join(path_base, arquivo_selecionado)

# ── Processamento ──────────────────────────────────────────────
if st.button("🚀 Processar"):
    with st.spinner("Processando... Isso pode levar alguns minutos para arquivos grandes."):
        analise = AnaliseEstoque(file_path)
        st.session_state["analise"] = analise
    st.success("✅ Processamento concluído!")

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
pasta_relatorios = "relatorios"
nome_arquivo = f"relatorio_{arquivo_selecionado.split('.')[0]}_{data_atual}.xlsx"


output_path = os.path.join(path_base, pasta_relatorios, nome_arquivo)
if not os.path.exists(os.path.join(path_base, pasta_relatorios)):
    os.makedirs(os.path.join(path_base, pasta_relatorios))
    
    
if st.button("📥 Exportar para Excel"):
    ok = analise.exportar_para_excel(output_path)
    if ok:
        st.success(f"Exportado em: {output_path}")