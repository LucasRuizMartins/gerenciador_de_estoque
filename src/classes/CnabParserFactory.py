# pyrefly: ignore [missing-import]
from src.classes.SingulareParser import SingulareParser


class CNABParserFactory:
    """
    Fábrica para instanciar o parser correto baseado no conteúdo do arquivo.
    Atualmente suporta o padrão Singulare (444 posições).
    """

    @staticmethod
    def get_parser(linhas):
        """
        Analisa o header e retorna a instância do parser adequada.
        
        Args:
            linhas (list): Lista de strings representando as linhas do arquivo.
            
        Returns:
            CNABParser: Uma instância de uma subclasse de CNABParser.
        """
        header = linhas[0]
        caracteres = len(header)
        #administrador = header[79:94].strip().lower()

        if caracteres == 444:
            return SingulareParser(linhas)

        # elif "outro_admin" in administrador:
        #     return OutroParser(linhas)

        raise ValueError(f"Padrão de cnab não suportado: {caracteres}")
