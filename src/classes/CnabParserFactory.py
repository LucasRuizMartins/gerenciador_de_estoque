from src.classes.SingulareParser import SingulareParser


class CNABParserFactory:

    @staticmethod
    def get_parser(linhas):
        header = linhas[0]
        caracteres = len(header)
        #administrador = header[79:94].strip().lower()

        if caracteres == 444:
            return SingulareParser(linhas)

        # elif "outro_admin" in administrador:
        #     return OutroParser(linhas)

        raise ValueError(f"Padrão de cnab não suportado: {caracteres}")