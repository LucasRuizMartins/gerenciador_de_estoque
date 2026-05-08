from abc import ABC, abstractmethod
import pandas as pd


class CNABParser(ABC):
    """
    Classe base abstrata para parsers de arquivos CNAB.
    Define a estrutura básica para leitura de header, corpo e trailer.
    """

    def __init__(self, linhas):
        """Inicializa o parser com uma lista de linhas do arquivo."""
        self.linhas = [l.strip() for l in linhas]
        self.header = self.linhas[0]
        self.trailer = self.linhas[-1]
        self.corpo = self.linhas[1:-1]

    @abstractmethod
    def parse_header(self):
        """Extrai informações do header (Primeira linha)."""
        pass

    @abstractmethod
    def parse_body(self):
        """Extrai informações do corpo (Registros de detalhe)."""
        pass

    def parse(self):
        """Orquestra o parsing completo do arquivo."""
        return {
            "header": self.parse_header(),
            "body": self.parse_body(),
            "trailer": self.trailer
        }

