import pandas as pd
import logging
# pyrefly: ignore [missing-import]
from src.metricas import MetricasGlobais, MetricasMensais, MetricasVencimento

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Classe responsável por exportar os resultados da análise para Excel."""

    def __init__(self, analise):
        self.analise = analise

    def exportar(self, output) -> bool:
        """Exporta métricas para Excel (arquivo ou buffer)."""
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_relatorio = self._construir_dataframe_relatorio()

                if df_relatorio.empty:
                    logger.warning("DataFrame principal vazio!")

                df_relatorio.to_excel(writer, sheet_name='Relatório Consolidado', index=False)
                self._formatar_planilha_excel(writer, df_relatorio)

                df_cedentes = self.analise.obter_cedentes_agrupados()
                if not df_cedentes.empty:
                    df_cedentes.to_excel(writer, sheet_name='Cedentes', index=False)

                df_recebiveis = self.analise.obter_recebiveis_agrupados()
                if not df_recebiveis.empty:
                    df_recebiveis.to_excel(writer, sheet_name='Recebíveis', index=False)

                writer.close()

            return True

        except Exception as e:
            logger.error("Erro na exportação: %s", e)
        return False
        
    def _construir_dataframe_relatorio(self) -> pd.DataFrame:
        """Constrói DataFrame com todas as métricas."""
        metricas = [
            "Nome Fundo",
            "Data de Referência",
            "Valor Nominal Total",
            "Vencido",
            "A vencer",
            "PDD",
            "Total",
            "Valor Aquisição Total",
            "Quantidade de Titulos",
            "Quantidade de Titulos a vencer",
            "Quantidade de titulos vencido",
            "Total de Sacados",
            "Total de Cedentes",
            "Valor Aquisição no Mês",
            "Quantidade Aquisição no Mês",
            "Ticket Médio Aquisicao a vencer",
            "Ticket Médio Aquisicao a vencido",
            "Ticket Médio Aquisicao a total",
            "Ticket Médio Presente a vencer",
            "Ticket Médio Presente a vencido",
            "Ticket Médio Presente a total",
            "Ticket Médio Nominal a vencer",
            "Ticket Médio Nominal a vencido",
            "Ticket Médio Nominal a total",            
            "taxa cessao mediana a vencer",
            "taxa cessao mediana vencido",
            "taxa cessao mediana total",            
            "Ultima Quinzena Ticket Médio Aquisicao a vencer",
            "Ultima Quinzena Ticket Médio Aquisicao a vencido",
            "Ultima Quinzena Ticket Médio Aquisicao a total",
            "Ultima Quinzena Ticket Médio Presente a vencer",
            "Ultima Quinzena Ticket Médio Presente a vencido",
            "Ultima Quinzena Ticket Médio Presente a total",
            "Ultima Quinzena Ticket Médio Nominal a vencer",
            "Ultima Quinzena Ticket Médio Nominal a vencido",
            "Ultima Quinzena Ticket Médio Nominal a total",
            "Prazo Médio TOTAL",
            "Prazo Médio Vencido",
            "Prazo Médio A vencer",
            "Ultima Quinzena Prazo Médio TOTAL",
            "Ultima Quinzena Prazo Médio Vencido",
            "Ultima Quinzena Prazo Médio A vencer",
            "Taxa Média do Mês",
        ]
        
        # Adicionar faixas de vencimento
        for situacao in ["A Vencer", "Vencido", "PDD A Vencer", "PDD Vencido"]:
            for faixa in ["0-15", "16-30", "31-60", "61-90", "91-120", "121-150", "151-180", "181-360", "+ 360"]:
                metricas.append(f"{situacao} {faixa} dias")
        
        valores_totais = self._obter_valores_totais()
        
        dados = {"Métrica": metricas, "Valor Total": valores_totais}
        
        df = pd.DataFrame(dados)
        
        # Adicionar colunas por tipo
        for tipo in sorted(self.analise.metricas_globais_por_tipo.keys()):
            df[tipo] = self._obter_valores_por_tipo(tipo)
        
        return df

    def _obter_valores_totais(self) -> list:
        """Obtém lista de valores totais."""
        m = self.analise.metricas_globais
        mm = self.analise.metricas_mensais
        mv = self.analise.metricas_vencimento
        
        valores = [
            m.nome_fundo,
            mm.data_ref.strftime("%Y/%m/%d"),
            m.valor_nominal,
            m.valor_vencido,
            m.valor_a_vencer,
            m.valor_pdd,
            m.valor_presente,
            m.valor_aquisicao,
            m.cont_transacoes,
            m.qtd_a_vencer,
            m.qtd_vencido,
            m.total_sacados,
            m.total_cedentes,
            mm.valor_aquisicao_mes,
            mm.qtd_aquisicao_mes,
            m.ticket_medio_aquisicao_a_vencer,
            m.ticket_medio_aquisicao_vencido,
            m.ticket_medio_aquisicao_total,
            m.ticket_medio_presente_a_vencer,
            m.ticket_medio_presente_vencido,
            m.ticket_medio_presente_total,
            m.ticket_medio_nominal_a_vencer,
            m.ticket_medio_nominal_vencido,
            m.ticket_medio_nominal_total,
            
            m.mediana_a_vencer,
            m.mediana_vencido,
            m.mediana_valor_aquisicao,
            
            m.ultima_quinzena_ticket_medio_aquisicao_a_vencer,
            m.ultima_quinzena_ticket_medio_aquisicao_vencido,
            m.ultima_quinzena_ticket_medio_aquisicao_total,
            m.ultima_quinzena_ticket_medio_presente_a_vencer,
            m.ultima_quinzena_ticket_medio_presente_vencido,
            m.ultima_quinzena_ticket_medio_presente_total,
            m.ultima_quinzena_ticket_medio_nominal_a_vencer,
            m.ultima_quinzena_ticket_medio_nominal_vencido,
            m.ultima_quinzena_ticket_medio_nominal_total,
            m.prazo_medio,
            m.prazo_medio_vencido,
            m.prazo_medio_a_vencer,
            m.ultima_quinzena_prazo_medio,
            m.ultima_quinzena_prazo_medio_vencido,
            m.ultima_quinzena_prazo_medio_a_vencer,
            mm.taxa_media_mes,
        ]
        
        # Adicionar valores de vencimento
        faixas_attr = [
            ('a_vencer', mv), ('vencido', mv),
            ('pdd_a_vencer', mv), ('pdd_vencido', mv)
        ]
        
        intervalos = ['0_15', '16_30', '31_60', '61_90', '91_120', '121_150', '151_180', '181_360', 'acima_360']
        
        for prefixo, obj in faixas_attr:
            for intervalo in intervalos:
                attr = f'{prefixo}_{intervalo}'
                valores.append(getattr(obj, attr, 0))
        
        return valores
    
    def _obter_valores_por_tipo(self, tipo: str) -> list:
        """Obtém lista de valores para um tipo específico."""
        mg = self.analise.metricas_globais_por_tipo.get(tipo, MetricasGlobais())
        mm = self.analise.metricas_mensais_por_tipo.get(tipo, MetricasMensais())
        mv = self.analise.metricas_vencimento_por_tipo.get(tipo, MetricasVencimento())
        
        valores = [
            self.analise.metricas_globais.nome_fundo,  # Nome Fundo
            self.analise.metricas_mensais.data_ref.strftime("%Y/%m/%d"),  # Data Referência
            mg.valor_nominal,
            mg.valor_vencido,
            mg.valor_a_vencer,
            mg.valor_pdd,
            mg.valor_presente,
            mg.valor_aquisicao,
            mg.cont_transacoes,
            mg.qtd_a_vencer,
            mg.qtd_vencido,
            mg.total_sacados,
            mg.total_cedentes,
            mm.valor_aquisicao_mes,
            mm.qtd_aquisicao_mes,
            mg.ticket_medio_aquisicao_a_vencer,
            mg.ticket_medio_aquisicao_vencido,
            mg.ticket_medio_aquisicao_total,
            mg.ticket_medio_presente_a_vencer,
            mg.ticket_medio_presente_vencido,
            mg.ticket_medio_presente_total,
            mg.ticket_medio_nominal_a_vencer,
            mg.ticket_medio_nominal_vencido,
            mg.ticket_medio_nominal_total,
            
            mg.mediana_a_vencer,
            mg.mediana_vencido,
            mg.mediana_valor_aquisicao,  
            
            mg.ultima_quinzena_ticket_medio_aquisicao_a_vencer,
            mg.ultima_quinzena_ticket_medio_aquisicao_vencido,
            mg.ultima_quinzena_ticket_medio_aquisicao_total,
            mg.ultima_quinzena_ticket_medio_presente_a_vencer,
            mg.ultima_quinzena_ticket_medio_presente_vencido,
            mg.ultima_quinzena_ticket_medio_presente_total,
            mg.ultima_quinzena_ticket_medio_nominal_a_vencer,
            mg.ultima_quinzena_ticket_medio_nominal_vencido,
            mg.ultima_quinzena_ticket_medio_nominal_total,
            mg.prazo_medio,
            mg.prazo_medio_vencido,
            mg.prazo_medio_a_vencer,
            mg.ultima_quinzena_prazo_medio,
            mg.ultima_quinzena_prazo_medio_vencido,
            mg.ultima_quinzena_prazo_medio_a_vencer,
            mm.taxa_media_mes,
        ]
        
        # Adicionar valores de vencimento com os nomes corretos dos atributos
        intervalos = ['0_15', '16_30', '31_60', '61_90', '91_120', '121_150', '151_180', '181_360', 'acima_360']
        
        # A Vencer
        for intervalo in intervalos:
            attr = f'a_vencer_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # Vencido
        for intervalo in intervalos:
            attr = f'vencido_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # PDD A Vencer
        for intervalo in intervalos:
            attr = f'pdd_a_vencer_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        # PDD Vencido
        for intervalo in intervalos:
            attr = f'pdd_vencido_{intervalo}'
            valores.append(getattr(mv, attr, 0))
        
        return valores
        
    def _formatar_planilha_excel(self, writer, df: pd.DataFrame) -> None:
        """Aplica formatação ao arquivo Excel."""
        workbook = writer.book
        worksheet = writer.sheets['Relatório Consolidado']
        
        # Formatos
        money_fmt = workbook.add_format({'num_format': '#,##0.00'})
        percent_fmt = workbook.add_format({'num_format': '0.00%'})
        integer_fmt = workbook.add_format({'num_format': '#,##0'})
        
        # Formato monetário padrão
        for col_num in range(1, len(df.columns)):
            worksheet.set_column(col_num, col_num, 18, money_fmt)
        
        # Formato inteiro para contagens
        metricas_inteiro = ["Quantidade de Titulos", "Quantidade Aquisição no Mês",
                           "Quantidade de Titulos a vencer", "Quantidade de titulos vencido",
                           "Total de Sacados", "Total de Cedentes"]
        
        for metrica in metricas_inteiro:
            indices = df[df['Métrica'] == metrica].index
            if len(indices) > 0:
                row = indices[0] + 1
                for col_num in range(1, len(df.columns)):
                    worksheet.write(row, col_num, df.iloc[indices[0], col_num], integer_fmt)
        
        # Formato percentual para taxa
        indices_taxa = df[df['Métrica'] == 'Taxa Média do Mês'].index
        if len(indices_taxa) > 0:
            row = indices_taxa[0] + 1
            for col_num in range(1, len(df.columns)):
                worksheet.write(row, col_num, df.iloc[indices_taxa[0], col_num], percent_fmt)
        
        # Largura da coluna de métricas
        worksheet.set_column(0, 0, 40)
