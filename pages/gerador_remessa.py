import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from datetime import datetime
from src.classes.cnab444_converter import CNAB444Converter
from src.global_var import MAP_OCORRENCIA, MAP_ESPECIE_TITULO

def carregar_configuracoes():
    """Tenta carregar do local, se não, busca no session_state."""
    if "config_fundos" in st.session_state:
        return st.session_state["config_fundos"]
        
    caminho_config = "config_fundos.json"
    if os.path.exists(caminho_config):
        try:
            with open(caminho_config, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

# Inicializa/Carrega a base de dados
CONFIG_FUNDOS = carregar_configuracoes()

st.set_page_config(page_title="Gerador de Remessa CNAB 444", page_icon="📄")

st.title("📄 Gerador de Remessa CNAB 444")
st.markdown("""
Esta ferramenta converte planilhas Excel para o formato **CNAB 444 (Remessa V2)**.
Selecione o fundo na barra lateral e faça o upload da planilha.
""")

st.markdown("---")

# Barra Lateral - Seleção de Fundo
st.sidebar.header("⚙️ Configuração")

# Opção de subir novo JSON de configuração
with st.sidebar.expander("🔑 Upload de Configurações"):
    arquivo_config = st.file_uploader("Subir config_fundos.json", type=["json"])
    if arquivo_config:
        try:
            novas_configs = json.load(arquivo_config)
            st.session_state["config_fundos"] = novas_configs
            CONFIG_FUNDOS = novas_configs
            st.success("✅ Configurações carregadas!")
        except Exception as e:
            st.error(f"❌ Erro no JSON: {e}")

if not CONFIG_FUNDOS:
    st.info("👋 Para começar, suba seu arquivo `config_fundos.json` no painel ao lado.")
    st.stop()

fundo_selecionado = st.sidebar.selectbox("Selecione o Fundo", list(CONFIG_FUNDOS.keys()))

# Carrega a configuração do fundo selecionado
config = CONFIG_FUNDOS[fundo_selecionado].copy()

# O número sequencial e datas costumam mudar, então deixamos eles editáveis ou automáticos
st.sidebar.markdown("---")
config["nr_sequencial_arquivo"] = st.sidebar.number_input("Nº Sequencial Arquivo", value=1, step=1)

# Mostra um resumo do que foi selecionado para conferência (opcional - modo leitura)
with st.sidebar.expander("🔍 Detalhes Técnicos do Fundo"):
    st.markdown(f"**Originador:** {config['nome_originador']}")
    st.markdown(f"**Cód. Originador:** `{config['codigo_originador']}`")
    st.markdown("---")
    st.markdown(f"**Banco:** {config['nome_banco']} ({config['numero_banco']})")
    
    agencia_completa = f"{config.get('agencia_cedente', '0000')}-{config.get('dig_verificador', '0')}"
    st.markdown(f"**Agência:** `{agencia_completa}`")
    
    conta_completa = f"{config.get('conta_corrente', '0')}-{config.get('dig_verificador_cc', '0')}"
    st.markdown(f"**Conta Corrente:** `{conta_completa}`")
    
    st.markdown(f"**Ident. Sistema:** {config.get('identificacao_sistema', 'MX')}")

# Parâmetros que podem variar por remessa
with st.sidebar.expander("🎯 Parâmetros da Remessa"):
    config["coobrigacao"] = st.selectbox(
        "Coobrigação", 
        ["01 - Com", "02 - Sem"], 
        index=0 if config["coobrigacao"] == "01" else 1
    ).split(" - ")[0]
    
    config["valor_retencao"] = st.number_input("Valor Retenção", value=config["valor_retencao"])

# Template de Excel na barra lateral
st.sidebar.markdown("---")
st.sidebar.subheader("📄 Template")

@st.cache_data
def gerar_template_excel():
    colunas = [
        "NOME_CEDENTE", "DOC_CEDENTE", "NOME_SACADO", "DOC_SACADO", 
        "ENDERECO", "CEP", "VALOR_NOMINAL", 
        "VALOR_PAGO","VALOR_PRESENTE", "VALOR_AQUISICAO", "DATA_VENCIMENTO_AJUSTADA", 
        "DATA_EMISSAO", "DATA_AQUISICAO", "NU_DOCUMENTO", "SEU_NUMERO","IDENTIFICACAO_OCORRENCIA","TIPO_RECEBIVEL"
    ]
    df_template = pd.DataFrame(columns=colunas)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Template')
    return output.getvalue()

st.sidebar.download_button(
    label="📥 Baixar Planilha Modelo",
    data=gerar_template_excel(),
    file_name="modelo_remessa_cnab444.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True
)

# Upload do Arquivo
arquivo_excel = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if arquivo_excel:
    try:
        df = pd.read_excel(arquivo_excel, dtype=str)
        st.success(f"✅ Arquivo '{arquivo_excel.name}' carregado com sucesso!")
        
        # Validação básica de colunas
        colunas_necessarias = [
            "NOME_SACADO", "DOC_SACADO", "VALOR_NOMINAL", 
            "DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO"
        ]
        faltando = [c for c in colunas_necessarias if c not in df.columns]
        
        if faltando:
            st.warning(f"⚠️ Atenção: Colunas obrigatórias não encontradas: {', '.join(faltando)}")
        
        # Dicionários de mapeamento (Rótulo amigável -> Código CNAB)
        MAPA_ESPECIES_UI = {f"{str(k).zfill(2)} - {v.upper()}": str(k).zfill(2) for k, v in MAP_ESPECIE_TITULO.items()}

        # Reaproveitando do global_var e formatando para a UI
        MAPA_OCORRENCIAS_UI = {f"{k} - {v}": k for k, v in MAP_OCORRENCIA.items()}

        st.write("### Edição dos Dados da Remessa")
        st.info("💡 Dica: Você pode alterar o tipo e a ocorrência diretamente na tabela.")

        # Mapas invertidos para carregar dados existentes
        MAPA_ESPECIES_INV = {v: k for k, v in MAPA_ESPECIES_UI.items()}
        MAPA_OCORRENCIAS_INV = {v: k for k, v in MAPA_OCORRENCIAS_UI.items()}

        # Preparação das colunas para o editor
        if "TIPO_RECEBIVEL" not in df.columns:
            df["TIPO_RECEBIVEL"] = "01 - DUPLICATA"
        else:
            # Tenta converter o que veio do Excel para o rótulo da UI
            # Se for um nome (ex: DUPLICATA), tenta mapear. Se for código (ex: 01), também.
            def mapear_especie(x):
                x_str = str(x).strip().zfill(2) if str(x).isdigit() else str(x).upper().strip()
                # Se já for um código no mapa invertido
                if x_str in MAPA_ESPECIES_INV: return MAPA_ESPECIES_INV[x_str]
                # Se for um nome que o conversor antigo conhecia
                especies_antigas = {"DUPLICATA": "01", "NP": "02", "CHEQUE": "51", "CONTRATO": "60"}
                cod = especies_antigas.get(x_str, "01")
                return MAPA_ESPECIES_INV.get(cod, "01 - DUPLICATA")
            
            df["TIPO_RECEBIVEL"] = df["TIPO_RECEBIVEL"].apply(mapear_especie)

        if "IDENTIFICACAO_OCORRENCIA" not in df.columns:
            df["IDENTIFICACAO_OCORRENCIA"] = MAPA_OCORRENCIAS_INV.get(config["identificacao_ocorrencia"], "01 - ENTRADA DE TÍTULOS (REMESSA)")
        else:
            df["IDENTIFICACAO_OCORRENCIA"] = df["IDENTIFICACAO_OCORRENCIA"].apply(
                lambda x: MAPA_OCORRENCIAS_INV.get(str(x).zfill(2), "01 - ENTRADA DE TÍTULOS (REMESSA)")
            )

        df_editado = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "TIPO_RECEBIVEL": st.column_config.SelectboxColumn(
                    "Tipo Recebível",
                    options=list(MAPA_ESPECIES_UI.keys()),
                    required=True,
                ),
                "IDENTIFICACAO_OCORRENCIA": st.column_config.SelectboxColumn(
                    "Ocorrência",
                    options=list(MAPA_OCORRENCIAS_UI.keys()),
                    required=True,
                )
            }
        )

        if st.button("🚀 Gerar Arquivo CNAB"):
            with st.spinner("Gerando remessa..."):
                # Converte os rótulos amigáveis de volta para códigos CNAB
                df_final = df_editado.copy()
                df_final["TIPO_RECEBIVEL"] = df_final["TIPO_RECEBIVEL"].map(MAPA_ESPECIES_UI)
                df_final["IDENTIFICACAO_OCORRENCIA"] = df_final["IDENTIFICACAO_OCORRENCIA"].map(MAPA_OCORRENCIAS_UI)

                converter = CNAB444Converter(config)
                linhas = converter.converter(df_final)
                conteudo = converter.get_conteudo(linhas)
                
                # Nome do arquivo sugerido: CB + DDMMAA + Seq
                data_hoje = datetime.today().strftime("%d%m%y")
                nome_sugerido = f"CB{data_hoje}{int(config['nr_sequencial_arquivo']):02d}.REM"
                
                st.info(f"✅ Remessa gerada com {len(linhas)-2} registros de detalhe.")
                
                st.download_button(
                    label="📥 Baixar Arquivo .REM",
                    data=conteudo,
                    file_name=nome_sugerido,
                    mime="text/plain",
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"❌ Erro ao processar arquivo: {e}")

else:
    st.info("Aguardando upload do arquivo Excel para começar.")
    
    with st.expander("ℹ️ Ajuda: Colunas Necessárias"):
        st.write("""
        Sua planilha deve conter as seguintes colunas (nomes exatos):
        - `NOME_CEDENTE`, `DOC_CEDENTE`
        - `NOME_SACADO`, `DOC_SACADO`
        - `TIPO_RECEBIVEL` (ex: DUPLICATA, CHEQUE)
        - `VALOR_NOMINAL`, `VALOR_PRESENTE`, `VALOR_AQUISICAO`
        - `DATA_VENCIMENTO_AJUSTADA`, `DATA_EMISSAO`, `DATA_AQUISICAO`
        - `NU_DOCUMENTO`, `SEU_NUMERO`
        """)
