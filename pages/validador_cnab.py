import streamlit as st
import pandas as pd
from datetime import datetime
# pyrefly: ignore [missing-import]
from src.classes.CnabParserFactory import CNABParserFactory
# pyrefly: ignore [missing-import]
from src.classes.Formater import Formater as fmt
# pyrefly: ignore [missing-import]
from src.global_var import MAP_OCORRENCIA, MAP_ESPECIE_TITULO
# pyrefly: ignore [missing-import]
import src.classes.analise_cnab as ac

st.title("📄 Leitor de Arquivo CNAB")


uploaded = st.file_uploader("Suba seu arquivo .rem ou .txt", type=["rem", "txt"])

if uploaded is None:
    st.stop()

# ── Parsing ─────────────────────────────────────
linhas = uploaded.read().decode("utf-8").splitlines()

parser = CNABParserFactory.get_parser(linhas)
resultado = parser.parse()

header = resultado["header"]
body = resultado["body"]
df = body["dataframe"]
erros = body["erros"]
trailer_raw = resultado["trailer"]
header_raw = parser.header  

# ── Detecção Automática de Finalidade ───────────
tem_baixa = False
for cod in df['identificacao_ocorrencia'].unique():
    desc = MAP_OCORRENCIA.get(cod, "").lower()
    if "baixa" in desc or cod in ['14', '71', '72', '73', '74', '75', '76', '77']:
        tem_baixa = True
        break

tipo_arquivo = st.radio(
    "**Finalidade deste arquivo:**", 
    ["Cessão (Aquisição)", "Liquidação (Baixas)"], 
    index=1 if tem_baixa else 0,
    horizontal=True,
    help="Detectado automaticamente com base nas ocorrências do arquivo."
)

if tem_baixa and tipo_arquivo == "Liquidação (Baixas)":
    st.success("✅ Detectamos ocorrências de **Baixa** no arquivo. Modo de Liquidação ativado.")
elif not tem_baixa and tipo_arquivo == "Cessão (Aquisição)":
    st.success("✅ Arquivo identificado como **Cessão/Aquisição**.")

st.markdown("---")

# ── Processamento de Datas e Taxas ────────────────
df['data_vencimento'] = pd.to_datetime(df['data_vencimento'], format='%d%m%y', errors='coerce')
df['data_aquisicao'] = pd.to_datetime(df['data_aquisicao'], format='%d%m%y', errors='coerce').fillna(header['data_operacao'])

# Cálculo do prazo (em dias) e taxas
df['prazo'] = (df['data_vencimento'] - df['data_aquisicao']).dt.days
df['prazo'] = df['prazo'].apply(lambda x: max(x, 1)) # Mínimo 1 dia para evitar divisão por zero

df['taxa_am'] = df.apply(
    lambda r: ac.calcular_taxa(r['valor_nominal'], r['valor_presente'], r['prazo']) 
    if r['valor_presente'] > 0 else 0, 
    axis=1
)
df['taxa_aa'] = df['taxa_am'].apply(ac.converter_para_anual)

# ── Header ─────────────────────────────────────
st.subheader("📋 Cabeçalho")

col1, col2, col3 = st.columns(3)

col1.metric("Banco", header["banco"])
col2.metric("Nº do Banco", header["numero_banco"])
col3.metric("Data da operação", header["data_operacao"].strftime("%d/%m/%Y"))

col1, col2 = st.columns(2)
col1.metric("Gestora", header["gestora"])

with st.expander("Ver header"):
    st.code(header_raw)

# ── BODY ─────────────────────────────────────
st.subheader(f"📝 Registros")

# ── KPIs ─────────────────────────────────────
st.write("### Identificação de ocorrência")

contagem = df['identificacao_ocorrencia'].value_counts().reset_index()
contagem.columns = ['Código','Quantidade']
contagem['Descrição'] = contagem['Código'].map(MAP_OCORRENCIA)
contagem = contagem[['Código','Descrição','Quantidade']]

# Resumo de Espécies
st.write("### Espécies de Títulos")
contagem_esp = df['especie_titulo'].value_counts().reset_index()
contagem_esp.columns = ['Código','Quantidade']
# Converte código string para int para bater com o MAP_ESPECIE_TITULO
contagem_esp['Descrição'] = contagem_esp['Código'].apply(lambda x: MAP_ESPECIE_TITULO.get(int(x) if str(x).isdigit() else x, "Desconhecido"))
contagem_esp = contagem_esp[['Código','Descrição','Quantidade']]

col1,col2 = st.columns(2)
with col1:
    st.write("**Ocorrências**")
    st.dataframe(contagem, hide_index=True, use_container_width=True)
with col2:
    st.write("**Espécies**")
    st.dataframe(contagem_esp, hide_index=True, use_container_width=True)

st.write("### Resumo de Ocorrências no Arquivo")
col1, col2, col3, col4, col5,col6 = st.columns(6)

col1.metric("Total Títulos", f"{len(df):,}")
col2.metric("Valor Nominal Total", fmt.format_br(df['valor_nominal'].sum()))
col3.metric("Valor Pago Total", fmt.format_br(df['valor_pago'].sum()))
col4.metric("Valor Presente Total", fmt.format_br(df['valor_presente'].sum()))
col5.metric("Contagem de Sacados", f"{df['doc_sacado'].nunique():,}")
col6.metric("Contagem de Cedentes", f"{df['cedente'].nunique():,}")

# ── Análise de Taxas e Projeções ────────────────
if tipo_arquivo == "Cessão (Aquisição)":
    st.subheader("📈 Análise de Taxas e Projeções")
    
    # Preparar dados para o módulo analise_cnab
    titulos_dict = df.rename(columns={'valor_nominal': 'vf', 'valor_presente': 'vp'}).to_dict('records')
    taxa_media = ac.taxa_equivalente_total(titulos_dict)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Taxa Média Ponderada", f"{taxa_media*100:.4f}% a.m.")
        st.caption(f"📊 Equivalente a **{ac.converter_para_anual(taxa_media)*100:.2f}% a.a.**")
        st.info("Taxa de equilíbrio que iguala o Valor Presente total da carteira.")

    with c2:
        # Slider com precisão de 0.01
        nova_taxa_pct = st.slider("Simular Nova Taxa (% a.m.)", 0.0, 15.0, float(taxa_media*100), 0.01, format="%.4f")
        
        # Input numérico para ajuste ultra-preciso
        nova_taxa_pct = st.number_input("Ajuste Fino da Taxa (% a.m.)", value=nova_taxa_pct, step=0.0001, format="%.4f")
        
        nova_taxa = nova_taxa_pct / 100
        nova_taxa_aa = ac.converter_para_anual(nova_taxa)
        
        st.write(f"📈 Taxa Simulada: **{nova_taxa_pct:.4f}% a.m.** | **{nova_taxa_aa*100:.2f}% a.a.**")
        
        projecao = ac.projetar_nova_taxa(titulos_dict, nova_taxa)
        
        sc1, sc2 = st.columns(2)
        sc1.metric("Novo VP Total", fmt.format_br(projecao['total_novo_vp']))
        sc2.metric("Diferença Total", fmt.format_br(projecao['diferenca']), delta=f"{projecao['diferenca']:.2f}")

    st.markdown("---")
else:
    st.info("💡 Análise de taxas ocultada (Modo Liquidação/Baixa).")


# ── Tabela ─────────────────────────────────────

st.dataframe(
    df.style.format({
        'valor_nominal': 'R$ {:,.2f}',
        'valor_pago': 'R$ {:,.2f}',
        'valor_presente': 'R$ {:,.2f}',
        'data_aquisicao': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "-",
        'data_vencimento': lambda x: x.strftime('%d/%m/%Y') if pd.notna(x) else "-",
        'doc_cedente': fmt.format_documento,
        'tipo_cedente': fmt.definir_tipo_documento,
        'doc_sacado': fmt.format_documento,
        'tipo_sacado': fmt.definir_tipo_documento,
        'especie_titulo': lambda x: f"{x} - {MAP_ESPECIE_TITULO.get(int(x) if str(x).isdigit() else x, '???')}",
        'taxa_am': lambda x: f"{x*100:.2f}%",
        'taxa_aa': lambda x: f"{x*100:.2f}%"
    }),
    use_container_width=True,
    hide_index=True
)

# ── Erros ─────────────────────────────────────
if erros:
    with st.expander(f"⚠️ {len(erros)} erros na leitura"):
        st.write(erros)

# ── Trailer ─────────────────────────────────────
with st.expander("Ver linha trailer"):
    st.code(trailer_raw)