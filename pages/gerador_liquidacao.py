# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
import json
import os
import tempfile
from datetime import date, datetime
# pyrefly: ignore [missing-import]
from src.classes.cnab444_converter import CNAB444Converter, CnabVariant
# pyrefly: ignore [missing-import]
from src.classes import liquidacao_estoque as liq
# pyrefly: ignore [missing-import]
from src.data_loader import carregar_arquivo
# pyrefly: ignore [missing-import]
from src.global_var import MAP_OCORRENCIA, MAP_ESPECIE_TITULO


def carregar_configuracoes():
    """Tenta carregar do session_state, senão do config_fundos.json local."""
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


CONFIG_FUNDOS = carregar_configuracoes()

OPCOES_OCORRENCIA = [liq.rotulo_ocorrencia(k) for k in MAP_OCORRENCIA]
OPCOES_ESPECIE = [liq.rotulo_especie(str(k).zfill(2)) for k in MAP_ESPECIE_TITULO]

COLUNAS_TABELA = [
    "INCLUIR", "LOTE", "NOME_CEDENTE", "NOME_SACADO", "DOC_SACADO", "NU_DOCUMENTO", "SEU_NUMERO",
    "TIPO_RECEBIVEL_ESTOQUE", "TIPO_RECEBIVEL", "IDENTIFICACAO_OCORRENCIA",
    "DATA_VENCIMENTO_AJUSTADA", "DATA_LIQUIDACAO", "VALOR_NOMINAL", "VALOR_PAGO",
    "DOC_CEDENTE", "VALOR_PRESENTE", "VALOR_AQUISICAO", "DATA_EMISSAO", "DATA_AQUISICAO",
]

st.title("💰 Gerador de CNAB de Liquidação (a partir do Estoque)")
st.markdown(
    "Suba o **arquivo de estoque**, escolha o vencimento a liquidar, ajuste a tabela "
    "(valor pago, tipo de recebível, tipo de baixa, exclusão de títulos) e gere o CNAB 444."
)
st.markdown("---")

# ── Sidebar: configuração do fundo ────────────────────────────────────────────
st.sidebar.header("⚙️ Configuração")
with st.sidebar.expander("🔑 Upload de Configurações"):
    arquivo_config = st.file_uploader("Subir config_fundos.json", type=["json"], key="liq_cfg_upload")
    if arquivo_config:
        try:
            CONFIG_FUNDOS = json.load(arquivo_config)
            st.session_state["config_fundos"] = CONFIG_FUNDOS
            st.success("✅ Configurações carregadas!")
        except Exception as e:
            st.error(f"❌ Erro no JSON: {e}")

if not CONFIG_FUNDOS:
    st.info("👋 Para começar, suba seu arquivo `config_fundos.json` no painel ao lado.")
    st.stop()

fundo_selecionado = st.sidebar.selectbox("Selecione o Fundo", list(CONFIG_FUNDOS.keys()), key="liq_fundo")
config = CONFIG_FUNDOS[fundo_selecionado].copy()
config["nr_sequencial_arquivo"] = st.sidebar.number_input("Nº Sequencial Arquivo", value=1, step=1, key="liq_seq")

with st.sidebar.expander("🎯 Parâmetros da Remessa"):
    config["coobrigacao"] = st.selectbox(
        "Coobrigação", ["01 - Com", "02 - Sem"],
        index=0 if config.get("coobrigacao", "01") == "01" else 1, key="liq_coob",
    ).split(" - ")[0]
    config["valor_retencao"] = st.number_input("Valor Retenção", value=config.get("valor_retencao", 0), key="liq_ret")

config["identificacao_ocorrencia"] = liq.OCORRENCIA_PADRAO

st.sidebar.markdown("---")
_variante_label = st.sidebar.radio(
    "Variante do layout:", options=["APEX_444", "QI_444"],
    captions=["BRL Trust / APEX GROUP V3", "QI (Singulare) — ago/2025"], key="liq_variante",
)
cnab_variant = CnabVariant(_variante_label)

# ── 1. Upload do estoque ──────────────────────────────────────────────────────
st.subheader("1️⃣ Arquivo de estoque")
arquivo = st.file_uploader("Estoque (.csv, .zip ou .xlsx)", type=["csv", "zip", "xlsx", "xls"], key="liq_estoque")

if not arquivo:
    st.info("Aguardando upload do estoque.")
    st.stop()

assinatura = (arquivo.name, arquivo.size)
if st.session_state.get("liq_assinatura") != assinatura:
    try:
        with st.spinner("Lendo estoque..."):
            bruto = carregar_arquivo(arquivo.getvalue(), arquivo.name)
            st.session_state["liq_estoque_df"] = liq.normalizar_estoque(bruto)
        st.session_state["liq_assinatura"] = assinatura
        st.session_state.pop("liq_base", None)
    except Exception as e:
        st.error(f"❌ Erro ao ler o estoque: {e}")
        st.stop()

estoque = st.session_state["liq_estoque_df"]
st.success(f"✅ {len(estoque):,} títulos lidos de '{arquivo.name}'.".replace(",", "."))

# ── 2. Filtro de vencimento ───────────────────────────────────────────────────
st.subheader("2️⃣ Vencimento a liquidar")
col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    modo_label = st.radio(
        "Quais títulos carregar?",
        ["Vencimento em uma data específica", "Todos os vencidos até a data"],
        horizontal=True, key="liq_modo",
    )
modo = "data" if modo_label.startswith("Vencimento") else "vencidos"
with col_b:
    data_ref = st.date_input(
        "Data de vencimento" if modo == "data" else "Vencidos até (inclusive)",
        value=date.today(), format="DD/MM/YYYY", key="liq_data_ref",
    )
with col_c:
    data_liq = st.date_input(
        "Data de liquidação (CNAB)", value=data_ref if modo == "data" else date.today(),
        format="DD/MM/YYYY", key=f"liq_data_liq_{modo}_{data_ref}",
    )

filtrado = liq.filtrar_vencimento(estoque, modo, data_ref)
st.caption(f"{len(filtrado):,} títulos encontrados para o filtro.".replace(",", "."))

if st.button("📥 Carregar títulos", type="primary", disabled=filtrado.empty, key="liq_carregar"):
    tabela, nao_mapeados = liq.montar_tabela_liquidacao(filtrado, data_liq, liq.OCORRENCIA_PADRAO)
    st.session_state["liq_base"] = tabela[COLUNAS_TABELA]
    st.session_state["liq_nao_mapeados"] = nao_mapeados
    st.session_state["liq_ver"] = st.session_state.get("liq_ver", 0) + 1

if "liq_base" not in st.session_state:
    st.stop()

# ── 3. Edição ─────────────────────────────────────────────────────────────────
st.subheader("3️⃣ Ajustes antes de gerar")

if st.session_state.get("liq_nao_mapeados"):
    st.warning(
        "⚠️ Tipos de recebível sem mapeamento (assumido **01 - DUPLICATA**; ajuste na tabela ou "
        "acrescente em `MAPA_TIPO_EXATO`): " + ", ".join(sorted(st.session_state["liq_nao_mapeados"]))
    )


def _escopo_mask(base: pd.DataFrame, escopo: str) -> pd.Series:
    if escopo == "Somente marcados em LOTE":
        return base["LOTE"].fillna(False).astype(bool)
    return base["INCLUIR"].fillna(False).astype(bool)


def _aplicar(coluna: str, valor, escopo: str):
    base = st.session_state["liq_base"].copy()
    base.loc[_escopo_mask(base, escopo), coluna] = valor
    st.session_state["liq_base"] = base
    st.session_state["liq_ver"] += 1


def _restaurar_valor(escopo: str):
    base = st.session_state["liq_base"].copy()
    m = _escopo_mask(base, escopo)
    base.loc[m, "VALOR_PAGO"] = base.loc[m, "VALOR_NOMINAL"]
    st.session_state["liq_base"] = base
    st.session_state["liq_ver"] += 1


def _marcar(coluna: str, valor: bool):
    base = st.session_state["liq_base"].copy()
    base[coluna] = valor
    st.session_state["liq_base"] = base
    st.session_state["liq_ver"] += 1


with st.expander("🛠️ Ações em lote", expanded=False):
    escopo = st.radio("Aplicar em:", ["Todos os títulos incluídos", "Somente marcados em LOTE"],
                      horizontal=True, key="liq_escopo")
    c1, c2 = st.columns(2)
    with c1:
        baixa_lote = st.selectbox("Tipo de baixa", OPCOES_OCORRENCIA,
                                  index=OPCOES_OCORRENCIA.index(liq.rotulo_ocorrencia(liq.OCORRENCIA_PADRAO)),
                                  key="liq_baixa_lote")
        st.button("Aplicar tipo de baixa", on_click=_aplicar,
                  args=("IDENTIFICACAO_OCORRENCIA", baixa_lote, escopo), key="liq_btn_baixa")
    with c2:
        esp_lote = st.selectbox("Tipo de recebível", OPCOES_ESPECIE, key="liq_esp_lote")
        st.button("Aplicar tipo de recebível", on_click=_aplicar,
                  args=("TIPO_RECEBIVEL", esp_lote, escopo), key="liq_btn_esp")
    b1, b2, b3, b4 = st.columns(4)
    b1.button("Valor pago = nominal", on_click=_restaurar_valor, args=(escopo,), key="liq_btn_val")
    b2.button("Incluir todos", on_click=_marcar, args=("INCLUIR", True), key="liq_btn_inc")
    b3.button("Excluir todos", on_click=_marcar, args=("INCLUIR", False), key="liq_btn_exc")
    b4.button("Limpar marcação LOTE", on_click=_marcar, args=("LOTE", False), key="liq_btn_lote")

base = st.session_state["liq_base"]
st.info("💡 Desmarque **INCLUIR** para excluir um título. Edite valor pago, tipo de recebível, "
        "tipo de baixa e data de liquidação direto na tabela.")

editado = st.data_editor(
    base,
    key=f"liq_editor_{st.session_state['liq_ver']}",
    hide_index=True,
    use_container_width=True,
    disabled=[c for c in COLUNAS_TABELA if c not in
              ("INCLUIR", "LOTE", "TIPO_RECEBIVEL", "IDENTIFICACAO_OCORRENCIA", "DATA_LIQUIDACAO", "VALOR_PAGO")],
    column_config={
        "INCLUIR": st.column_config.CheckboxColumn("Incluir", default=True),
        "LOTE": st.column_config.CheckboxColumn("Lote"),
        "TIPO_RECEBIVEL_ESTOQUE": st.column_config.TextColumn("Tipo (estoque)"),
        "TIPO_RECEBIVEL": st.column_config.SelectboxColumn("Tipo Recebível (CNAB)", options=OPCOES_ESPECIE, required=True),
        "IDENTIFICACAO_OCORRENCIA": st.column_config.SelectboxColumn("Tipo de baixa", options=OPCOES_OCORRENCIA, required=True),
        "DATA_VENCIMENTO_AJUSTADA": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
        "DATA_LIQUIDACAO": st.column_config.DateColumn("Data Liquidação", format="DD/MM/YYYY"),
        "DATA_EMISSAO": st.column_config.DateColumn("Emissão", format="DD/MM/YYYY"),
        "DATA_AQUISICAO": st.column_config.DateColumn("Aquisição", format="DD/MM/YYYY"),
        "VALOR_NOMINAL": st.column_config.NumberColumn("Valor Nominal", format="R$ %.2f"),
        "VALOR_PAGO": st.column_config.NumberColumn("Valor Pago", format="R$ %.2f", min_value=0.0),
        "VALOR_PRESENTE": st.column_config.NumberColumn("Valor Presente", format="R$ %.2f"),
        "VALOR_AQUISICAO": st.column_config.NumberColumn("Valor Aquisição", format="R$ %.2f"),
    },
)
# Persiste as edições para que ações em lote partam do estado mais recente
st.session_state["liq_base"] = editado

sel = editado[editado["INCLUIR"].fillna(False).astype(bool)]
m1, m2, m3 = st.columns(3)
m1.metric("Títulos selecionados", f"{len(sel):,}".replace(",", "."))
m2.metric("Total nominal", f"R$ {sel['VALOR_NOMINAL'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
m3.metric("Total pago", f"R$ {pd.to_numeric(sel['VALOR_PAGO'], errors='coerce').sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# ── 4. Geração ────────────────────────────────────────────────────────────────
st.subheader("4️⃣ Gerar CNAB")
if st.button("🚀 Gerar Arquivo CNAB de Liquidação", key="liq_gerar", disabled=sel.empty):
    df_final = liq.preparar_para_cnab(editado)
    sem_data = int(df_final["DATA_LIQUIDACAO"].isna().sum())
    if sem_data:
        st.warning(f"⚠️ {sem_data} título(s) sem Data de Liquidação (serão gravados como 000000).")

    nome_fundo_limpo = fundo_selecionado.replace(" ", "_").upper()
    nome_sugerido = f"CB{datetime.today().strftime('%d%m%y')}{int(config['nr_sequencial_arquivo']):02d}_{nome_fundo_limpo}_LIQ.REM"

    temp_file = tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="ascii", newline="")
    temp_path = temp_file.name
    try:
        with st.spinner("Gerando remessa..."):
            converter = CNAB444Converter(config, variant=cnab_variant)
            converter.converter_para_fluxo(df_final, temp_file, chunk_size=50000)
            temp_file.close()
            with open(temp_path, "rb") as f_read:
                conteudo = f_read.read()
        st.success(f"✅ Remessa de liquidação gerada com {len(df_final)} registros de detalhe.")
        st.download_button("📥 Baixar Arquivo .REM", data=conteudo, file_name=nome_sugerido,
                           mime="text/plain", use_container_width=True)
    except Exception as e:
        st.error(f"❌ Erro durante a geração do arquivo: {e}")
    finally:
        if not temp_file.closed:
            temp_file.close()
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception:
                pass
