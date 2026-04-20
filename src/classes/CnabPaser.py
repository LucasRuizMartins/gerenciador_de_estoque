from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd

class CNABParser(ABC):
    
    
    def __init__(self, linhas):
        self.linhas = [l.strip() for l in linhas]
        self.header = self.linhas[0]
        self.trailer = self.linhas[-1]
        self.corpo = self.linhas[1:-1]

       
        
    @abstractmethod
    def parse_header(self):
        pass

    @abstractmethod
    def parse_body(self):
        pass

    def parse(self):
        return {
            "header": self.parse_header(),
            "body": self.parse_body(),
            "trailer": self.trailer
        }
        
