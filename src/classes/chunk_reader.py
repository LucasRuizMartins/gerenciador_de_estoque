import logging
import pandas as pd
import numpy as np
from zipfile import ZipFile
from typing import Iterator

logger = logging.getLogger(__name__)

class ChunkReader:
    """
    Classe responsável por ler e preparar chunks de dados de arquivos
    CSV, Excel ou ZIP para análise de estoque.
    """
    
    COLUNAS_ESSENCIAIS = [
        'TIPO_RECEBIVEL', 'VALOR_NOMINAL', 'VALOR_PRESENTE', 'VALOR_AQUISICAO',
        'DATA_REFERENCIA', 'DATA_AQUISICAO', 'DATA_VENCIMENTO_ORIGINAL',
        'PRAZO_ATUAL', 'PRAZO', 'SITUACAO_RECEBIVEL', 'TAXA_CESSAO',
        'DOC_CEDENTE', 'NOME_CEDENTE', 'NOME_FUNDO', 'DOC_SACADO', 'NOME_SACADO', 'VALOR_PDD'
    ]    
    
    CHUNK_SIZE = 500_000

    DTYPE_MAP = {
        'TIPO_RECEBIVEL': 'category',
        'SITUACAO_RECEBIVEL': 'category',
        'DOC_CEDENTE': 'category',
        'NOME_CEDENTE': 'category',
        'DOC_SACADO': 'category',
        'NOME_SACADO': 'category',
        'NOME_FUNDO': 'category',
        'VALOR_NOMINAL': 'float64',
        'VALOR_PRESENTE': 'float64',
        'VALOR_AQUISICAO': 'float64',
        'PRAZO_ATUAL': 'int16',
        'TAXA_CESSAO': 'float64',
        'VALOR_PDD': 'float64',
    }

    def __init__(self, path: str):
        self.path = path
        self.data_ref = self._determinar_data_referencia()
        
    def _determinar_data_referencia(self) -> pd.Timestamp:
        """Determina a data de referência usando apenas o primeiro registro válido."""
        data_ref_atual = pd.Timestamp.now().replace(day=1)
        try:
            chunk = next(self._obter_chunk_iterator(), None)
            if chunk is not None and not chunk.empty:
                data_str = chunk.get('DATA_REFERENCIA', [None])[0]
                data_ref = pd.to_datetime(data_str, dayfirst=True, errors='coerce')
                if pd.notna(data_ref):
                    data_ref_atual = data_ref
        except Exception as e:
            logger.debug("Erro ao determinar data de referência: %s", e)
            pass
        return data_ref_atual

    def iter_chunks(self) -> Iterator[pd.DataFrame]:
        """Retorna um iterador de chunks já preparados."""
        chunk_iterator = self._obter_chunk_iterator()
        for chunk_num, chunk in enumerate(chunk_iterator, 1):
            if chunk_num % 10 == 0:
                logger.debug("Processando chunk %d...", chunk_num)
            
            chunk = self._preparar_chunk(chunk)
            yield chunk

    def _obter_chunk_iterator(self) -> Iterator[pd.DataFrame]:
        """Retorna iterador de chunks baseado no tipo de arquivo."""
        extensao = self.path.lower()
        if extensao.endswith('.csv'):
            return self._chunks_csv()
        elif extensao.endswith(('.xlsx', '.xls')):
            return self._chunks_excel()
        elif extensao.endswith('.zip'):
            return self._chunks_zip()
        else:
            raise ValueError("Formato não suportado. Use .csv, .xlsx, .xls ou .zip")

    def _chunks_csv(self) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivo CSV."""
        return pd.read_csv(
            self.path,
            encoding='ISO-8859-1',
            on_bad_lines='skip',
            delimiter=';',
            decimal=',',
            thousands='.',
            low_memory=False,
            chunksize=self.CHUNK_SIZE,
            usecols=lambda col: col in self.COLUNAS_ESSENCIAIS
        )

    def _chunks_excel(self) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivo Excel."""
        df = pd.read_excel(self.path, usecols=lambda col: col in self.COLUNAS_ESSENCIAIS)
        for i in range(0, len(df), self.CHUNK_SIZE):
            yield df.iloc[i:i + self.CHUNK_SIZE].copy()

    def _chunks_zip(self) -> Iterator[pd.DataFrame]:
        """Gera chunks de arquivos CSV dentro de ZIP."""
        with ZipFile(self.path) as z:
            for filename in z.namelist():
                if filename.endswith('.csv'):
                    logger.info("Processando arquivo: %s", filename)
                    with z.open(filename) as f:
                        yield from pd.read_csv(
                            f,
                            encoding='ISO-8859-1',
                            delimiter=';',
                            decimal=',',
                            thousands='.',
                            low_memory=False,
                            chunksize=self.CHUNK_SIZE,
                            on_bad_lines='skip',
                            usecols=lambda col: col in self.COLUNAS_ESSENCIAIS
                        )

    def _preparar_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Prepara chunk com conversões de tipo otimizadas."""
        self._converter_datas(chunk)
        self._converter_tipos(chunk)
        self._adicionar_colunas_calculadas(chunk)
        return chunk

    def _converter_datas(self, chunk: pd.DataFrame) -> None:
        """Converte colunas de data."""
        colunas_data = ['DATA_REFERENCIA', 'DATA_AQUISICAO', 'DATA_VENCIMENTO_ORIGINAL']
        for col in colunas_data:
            if col in chunk.columns:
                chunk[col] = pd.to_datetime(chunk[col], dayfirst=True, errors='coerce')

    def _converter_tipos(self, chunk: pd.DataFrame) -> None:
        """Converte tipos de dados das colunas."""
        for col, dtype in self.DTYPE_MAP.items():
            if col not in chunk.columns:
                continue
            
            if dtype == 'category':
                chunk[col] = chunk[col].astype('category')
            elif dtype in ['float32', 'float64']:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(dtype)
            elif dtype in ['int16', 'int32']:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0).astype(dtype)

    def _adicionar_colunas_calculadas(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Adiciona colunas calculadas ao dataframe."""
        if 'VALOR_AQUISICAO' in chunk.columns and 'TAXA_CESSAO' in chunk.columns:
            chunk['TAXA_MEDIA'] = (
                pd.to_numeric(chunk['VALOR_AQUISICAO'], errors='coerce').fillna(0) *
                pd.to_numeric(chunk['TAXA_CESSAO'], errors='coerce').fillna(0)
            ).astype('float64')
        
        if 'PRAZO' in chunk.columns and 'VALOR_AQUISICAO' in chunk.columns:
            chunk['PRAZO_MEDIO'] = (chunk['VALOR_AQUISICAO'] * chunk['PRAZO']).astype('float64')
            prazo_safe = chunk['PRAZO'].replace(0, np.nan)
            chunk['TAXA_DE_CESSAO'] = ((chunk['VALOR_NOMINAL'] / chunk['VALOR_AQUISICAO']) ** (252 / prazo_safe) - 1) * 100
        
        return chunk
