# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from datetime import datetime
# pyrefly: ignore [missing-import]
from src.classes.cnab444_converter import CNAB444Converter
# pyrefly: ignore [missing-import]
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

# st.set_page_config(page_title="Gerador de Remessa CNAB 444", page_icon="📄") # Removido para não conflitar com app.py

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

# Upload do Arquivo (Suporta Excel .xlsx ou CSV para alta performance)
arquivo_upload = st.file_uploader("Selecione o arquivo (Excel .xlsx ou CSV .csv)", type=["xlsx", "csv"])

if arquivo_upload:
    try:
        nome_arquivo = arquivo_upload.name.lower()
        if nome_arquivo.endswith(".csv"):
            # Detecta o separador correto (, ou ;) analisando a primeira linha
            primeira_linha = arquivo_upload.readline()
            arquivo_upload.seek(0)
            
            try:
                linha_str = primeira_linha.decode("utf-8")
            except Exception:
                linha_str = primeira_linha.decode("iso-8859-1", errors="ignore")
                
            separador = ";" if linha_str.count(";") > linha_str.count(",") else ","
            
            # Detecta se o CSV possui cabeçalho
            # Se não contiver palavras como 'cedente', 'sacado', 'valor', 'data', 'documento', assume que não tem cabeçalho
            palavras_chave = ["cedente", "sacado", "valor", "data", "documento", "cep", "tipo"]
            tem_cabecalho = any(p in linha_str.lower() for p in palavras_chave)
            
            if tem_cabecalho:
                try:
                    df = pd.read_csv(arquivo_upload, dtype=str, sep=separador, encoding="utf-8")
                except UnicodeDecodeError:
                    arquivo_upload.seek(0)
                    df = pd.read_csv(arquivo_upload, dtype=str, sep=separador, encoding="iso-8859-1")
            else:
                # Não possui cabeçalho: lê com header=None e renomeia colunas por posição
                try:
                    df = pd.read_csv(arquivo_upload, dtype=str, sep=separador, encoding="utf-8", header=None)
                except UnicodeDecodeError:
                    arquivo_upload.seek(0)
                    df = pd.read_csv(arquivo_upload, dtype=str, sep=separador, encoding="iso-8859-1", header=None)
                
                # Mapeamento padrão baseado no layout posicional de 16 colunas
                mapeamento_colunas = {
                    0: "NOME_CEDENTE",
                    1: "DOC_CEDENTE",
                    2: "NOME_SACADO",
                    3: "DOC_SACADO",
                    4: "VALOR_NOMINAL",
                    5: "VALOR_PAGO",
                    6: "VALOR_AQUISICAO",
                    7: "DATA_VENCIMENTO_AJUSTADA",
                    8: "DATA_EMISSAO",
                    9: "DATA_AQUISICAO",
                    10: "NU_DOCUMENTO",
                    11: "SEU_NUMERO",
                    12: "ENDERECO",
                    13: "CEP",
                    14: "IDENTIFICACAO_OCORRENCIA",
                    15: "TIPO_RECEBIVEL"
                }
                df.rename(columns=mapeamento_colunas, inplace=True)
                df["VALOR_PRESENTE"] = df["VALOR_AQUISICAO"]
        else:
            df = pd.read_excel(arquivo_upload, dtype=str)
            
        # Limpa espaços em branco dos nomes das colunas para evitar incompatibilidade
        df.columns = df.columns.str.strip()
        
        # OTIMIZAÇÃO: Remove linhas totalmente vazias ou com nome do sacado vazio (linhas extras de fim de arquivo)
        df.dropna(how="all", inplace=True)
        if "NOME_SACADO" in df.columns:
            df = df[df["NOME_SACADO"].notna() & (df["NOME_SACADO"].astype(str).str.strip() != "")]
            
        st.success(f"✅ Arquivo '{arquivo_upload.name}' carregado com sucesso!")
        
        # Pré-conversão das colunas de data.
        # ATENÇÃO: pd.read_excel com dtype=str retorna datas Excel como strings no formato
        # "YYYY-MM-DD HH:MM:SS" (ex: "2026-05-06 00:00:00"). O dayfirst=True do pd.to_datetime
        # não é suficiente para todos os casos, por isso tentamos formatos explícitos primeiro.
        FORMATOS_LEITURA = [
            "%Y-%m-%d %H:%M:%S",  # Excel via dtype=str (mais comum)
            "%Y-%m-%dT%H:%M:%S",  # ISO 8601 com T
            "%d/%m/%Y", "%d/%m/%y",
            "%d-%m-%Y", "%d-%m-%y",
            "%Y-%m-%d",
        ]
        INVALIDOS_DATA = {"", "nan", "NaT", "None", "none", "NAT", "NAN"}
        for col_data in ["DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO", "DATA_AQUISICAO", "DATA_LIQUIDACAO"]:
            if col_data not in df.columns:
                continue
            s = df[col_data].fillna("").astype(str).str.strip()
            valido = ~s.isin(INVALIDOS_DATA)
            dt = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
            for fmt in FORMATOS_LEITURA:
                mask = dt.isna() & valido
                if not mask.any():
                    break
                parsed = pd.to_datetime(s[mask], format=fmt, errors="coerce")
                dt[mask] = dt[mask].where(parsed.isna(), parsed)
            # Fallback: inferência genérica do pandas com dayfirst=True
            still_na = dt.isna() & valido
            if still_na.any():
                dt[still_na] = pd.to_datetime(s[still_na], dayfirst=True, errors="coerce")
            df[col_data] = dt
        
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

        # OTIMIZAÇÃO: Proteger o Streamlit contra excesso de linhas no st.data_editor (evita travamento de browser)
        limite_editor = 100
        tamanho_total = len(df)
        if tamanho_total > limite_editor:
            st.warning(f"⚠️ Planilha grande detectada ({tamanho_total} linhas). Exibindo as primeiras {limite_editor} linhas no editor interativo para garantir alta performance. As edições nesta tabela serão aplicadas aos primeiros registros, e o arquivo completo será gerado em segundo plano.")
            df_para_editar = df.head(limite_editor).copy()
        else:
            df_para_editar = df.copy()

        df_editado = st.data_editor(
            df_para_editar,
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
                # OTIMIZAÇÃO: Reconstrói o df_final aplicando edições ou usando o dataframe original
                if tamanho_total > limite_editor:
                    df_final = df.copy()
                    df_final.iloc[:limite_editor] = df_editado
                else:
                    df_final = df_editado.copy()

                # Converte os rótulos amigáveis de volta para códigos CNAB
                df_final["TIPO_RECEBIVEL"] = df_final["TIPO_RECEBIVEL"].map(MAPA_ESPECIES_UI)
                df_final["IDENTIFICACAO_OCORRENCIA"] = df_final["IDENTIFICACAO_OCORRENCIA"].map(MAPA_OCORRENCIAS_UI)

                # Re-converte as colunas de data para datetime64 usando formato explícito DDMMYYYY/brasileiro.
                # O st.data_editor serializa datas de volta para string no formato americano (ex: 2026-05-18),
                # então precisamos re-parsear com format="%Y-%m-%d" (ISO, sem ambiguidade) para garantir a data correta.
                COLUNAS_DATA = ["DATA_VENCIMENTO_AJUSTADA", "DATA_EMISSAO", "DATA_AQUISICAO", "DATA_LIQUIDACAO"]
                # Formatos em ordem de prioridade:
                # 1. Com timestamp (pd.read_excel + dtype=str retorna "2026-05-06 00:00:00")
                # 2. Brasileiros DD/MM/YYYY
                # 3. ISO YYYY-MM-DD
                # 4. Americano MM/DD/YYYY (último recurso)
                FORMATOS_DATA = [
                    "%Y-%m-%d %H:%M:%S",  # Excel via dtype=str → "2026-05-06 00:00:00"
                    "%Y-%m-%dT%H:%M:%S",  # ISO 8601 com T
                    "%d/%m/%Y", "%d/%m/%y",
                    "%d-%m-%Y", "%d-%m-%y",
                    "%Y-%m-%d",
                    "%m/%d/%Y", "%m-%d-%Y",
                ]
                INVALIDOS = {"", "nan", "NaT", "None", "none", "NAT", "NAN"}
                for col_data in COLUNAS_DATA:
                    if col_data not in df_final.columns:
                        continue
                    col = df_final[col_data]
                    # Se já for datetime64, nada a fazer
                    if pd.api.types.is_datetime64_any_dtype(col):
                        continue
                    # Tenta formatos explícitos em ordem
                    dt_parsed = pd.Series(pd.NaT, index=col.index, dtype="datetime64[ns]")
                    s_str = col.fillna("").astype(str).str.strip()
                    valido = ~s_str.isin(INVALIDOS)
                    for fmt in FORMATOS_DATA:
                        mask = dt_parsed.isna() & valido
                        if not mask.any():
                            break
                        parsed = pd.to_datetime(s_str[mask], format=fmt, errors="coerce")
                        dt_parsed[mask] = dt_parsed[mask].where(parsed.isna(), parsed)
                    # Fallback final: inferência livre do pandas para qualquer remanescente
                    still_na = dt_parsed.isna() & valido
                    if still_na.any():
                        parsed_fb = pd.to_datetime(s_str[still_na], dayfirst=True, errors="coerce")
                        dt_parsed[still_na] = dt_parsed[still_na].where(parsed_fb.isna(), parsed_fb)
                    df_final[col_data] = dt_parsed

                # Nome do arquivo sugerido: CB + DDMMAA + Seq + Nome do Fundo
                data_hoje = datetime.today().strftime("%d%m%y")
                nome_fundo_limpo = fundo_selecionado.replace(" ", "_").upper()
                nome_sugerido = f"CB{data_hoje}{int(config['nr_sequencial_arquivo']):02d}_{nome_fundo_limpo}.REM"

                import tempfile
                # Criamos um arquivo temporário no disco para gravação em chunks
                temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="ascii", newline="")
                temp_path = temp_file.name
                
                try:
                    converter = CNAB444Converter(config)
                    # Processa e grava o DataFrame em chunks de 50.000 linhas
                    converter.converter_para_fluxo(df_final, temp_file, chunk_size=50000)
                    temp_file.close()

                    # Lemos o arquivo binariamente para passar ao st.download_button
                    with open(temp_path, "rb") as f_read:
                        conteudo_bytes = f_read.read()
                    
                    st.info(f"✅ Remessa gerada com {tamanho_total} registros de detalhe.")
                    
                    st.download_button(
                        label="📥 Baixar Arquivo .REM",
                        data=conteudo_bytes,
                        file_name=nome_sugerido,
                        mime="text/plain",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Erro durante a geração do arquivo: {e}")
                finally:
                    # Garante que o arquivo temporário é deletado do disco
                    if os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except Exception:
                            pass
                
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
