import streamlit as st 


def componente_upload_processamento(label, ClasseProcessadora, chave_session):
    """
    label: Texto que aparece no uploader
    ClasseProcessadora: A classe que será instanciada (ex: AnaliseEstoque, AnaliseFIDC)
    chave_session: Nome da chave no st.session_state (ex: 'analise_atual')
    """
    arquivo = st.file_uploader(label, type=['zip', 'csv', 'xlsx'])

    if arquivo is None:
        st.info("Aguardando arquivo...")
        return False

    if st.button(f"🚀 Processar {arquivo.name}"):
        with st.spinner("Executando lógica de negócio..."):
            try:
                # Instancia a classe genérica passada no argumento
                objeto_processado = ClasseProcessadora(arquivo)
                st.session_state[chave_session] = objeto_processado
                st.success("✅ Sucesso!")
                return True
            except Exception as e:
                st.error(f"Erro: {e}")
                return False
    
    return chave_session in st.session_state