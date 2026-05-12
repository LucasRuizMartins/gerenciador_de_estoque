"""
Testes para analise_cnab.py
Validados contra os dados reais da planilha Arquivo_de_Validação_Moovpay.xlsx
"""

import pytest
from src.classes.analise_cnab import (
    calcular_taxa,
    calcular_vp,
    calcular_vf,
    processar_titulos,
    projetar_nova_taxa,
    taxa_equivalente_total,
)

TOLERANCE = 1e-4  # 4 casas decimais — suficiente para valores financeiros


# ─────────────────────────────────────────────
# calcular_taxa
# ─────────────────────────────────────────────

class TestCalcularTaxa:
    # Valores extraídos diretamente da planilha (coluna Taxa a.m.)
    @pytest.mark.parametrize("vf, vp, prazo, taxa_esperada", [
        (63.33,  56.36,  76, 0.047101744),
        (39.99,  35.59,  76, 0.047087385),
        (115.96, 103.20, 76, 0.047092232),
        (55.54,  49.43,  91, 0.039169403),
        (96.00,  85.44,  91, 0.039165244),
        (88.00,  78.32,  96, 0.037088032),
        (8.90,   8.19,   76, 0.033361816),  # título com taxa menor (fora do padrão)
    ])
    def test_taxa_contra_planilha(self, vf, vp, prazo, taxa_esperada):
        assert calcular_taxa(vf, vp, prazo) == pytest.approx(taxa_esperada, abs=TOLERANCE)

    def test_vf_igual_vp_retorna_zero(self):
        """Sem deságio → taxa zero."""
        assert calcular_taxa(100, 100, 30) == pytest.approx(0.0, abs=TOLERANCE)

    def test_prazo_exato_30_dias(self):
        """Com prazo = 30 dias a taxa deve ser exatamente (VF/VP) - 1."""
        assert calcular_taxa(110, 100, 30) == pytest.approx(0.10, abs=TOLERANCE)

    def test_taxa_cresce_com_deságio_maior(self):
        """Quanto maior o deságio, maior a taxa."""
        taxa_pequena = calcular_taxa(110, 105, 30)
        taxa_grande  = calcular_taxa(110,  90, 30)
        assert taxa_grande > taxa_pequena

    def test_taxa_cai_com_prazo_maior(self,):
        """Mesmo deságio em prazo maior implica taxa menor."""
        taxa_curta = calcular_taxa(110, 100, 30)
        taxa_longa = calcular_taxa(110, 100, 60)
        assert taxa_longa < taxa_curta

    def test_prazo_zero_ou_negativo_retorna_zero(self):
        """Evita erro de divisão por zero retornando taxa neutra."""
        assert calcular_taxa(100, 90, 0) == 0.0
        assert calcular_taxa(100, 90, -5) == 0.0

    def test_vp_zero_ou_negativo_retorna_zero(self):
        """Evita erro de divisão por zero em VP inválido."""
        assert calcular_taxa(100, 0, 30) == 0.0
        assert calcular_taxa(100, -10, 30) == 0.0


# ─────────────────────────────────────────────
# calcular_vp
# ─────────────────────────────────────────────

class TestCalcularVP:
    # Coluna "Novo VP" da planilha usa nova_taxa = 0.5 (50% a.m.)
    @pytest.mark.parametrize("vf, prazo, novo_vp_esperado", [
        (63.33,  76, 22.67),
        (39.99,  76, 14.32),
        (115.96, 76, 41.52),
        (55.54,  91, 16.24),
        (96.00,  91, 28.06),
    ])
    def test_novo_vp_contra_planilha(self, vf, prazo, novo_vp_esperado):
        assert calcular_vp(vf, 0.5, prazo) == pytest.approx(novo_vp_esperado, rel=0.01)

    def test_taxa_zero_retorna_vf(self):
        """Com taxa zero VP deve ser igual ao VF."""
        assert calcular_vp(100, 0.0, 60) == pytest.approx(100.0, abs=TOLERANCE)

    def test_vp_menor_que_vf(self):
        """VP sempre menor que VF quando taxa > 0."""
        assert calcular_vp(100, 0.05, 30) < 100

    def test_vp_diminui_com_taxa_maior(self):
        """Taxa maior → VP menor para mesmo VF e prazo."""
        vp_baixa = calcular_vp(100, 0.03, 60)
        vp_alta  = calcular_vp(100, 0.10, 60)
        assert vp_alta < vp_baixa

    def test_vp_diminui_com_prazo_maior(self):
        """Prazo maior → VP menor para mesmo VF e taxa."""
        vp_curto = calcular_vp(100, 0.05, 30)
        vp_longo = calcular_vp(100, 0.05, 90)
        assert vp_longo < vp_curto

    def test_prazo_zero_usa_um_dia(self):
        """Garante que prazo 0 não quebra o cálculo do VP."""
        assert calcular_vp(100, 0.05, 0) == calcular_vp(100, 0.05, 1)


# ─────────────────────────────────────────────
# calcular_vf
# ─────────────────────────────────────────────

class TestCalcularVF:
    def test_inverso_de_calcular_vp(self):
        """calcular_vf(calcular_vp(vf)) deve retornar o VF original."""
        vf_original = 150.0
        taxa, prazo = 0.047, 76
        vp = calcular_vp(vf_original, taxa, prazo)
        assert calcular_vf(vp, taxa, prazo) == pytest.approx(vf_original, abs=TOLERANCE)

    def test_taxa_zero_retorna_vp(self):
        assert calcular_vf(100, 0.0, 60) == pytest.approx(100.0, abs=TOLERANCE)

    def test_vf_maior_que_vp(self):
        assert calcular_vf(100, 0.05, 30) > 100

    def test_vf_cresce_com_prazo_maior(self):
        vf_curto = calcular_vf(100, 0.05, 30)
        vf_longo = calcular_vf(100, 0.05, 90)
        assert vf_longo > vf_curto


# ─────────────────────────────────────────────
# processar_titulos
# ─────────────────────────────────────────────

class TestProcessarTitulos:
    TITULOS = [
        {"vf": 63.33,  "vp": 56.36, "prazo": 76},
        {"vf": 115.96, "vp": 103.20, "prazo": 76},
        {"vf": 55.54,  "vp": 49.43, "prazo": 91},
    ]

    def test_retorna_mesma_quantidade(self):
        resultado = processar_titulos(self.TITULOS)
        assert len(resultado) == len(self.TITULOS)

    def test_campos_originais_preservados(self):
        resultado = processar_titulos(self.TITULOS)
        for original, processado in zip(self.TITULOS, resultado):
            assert processado["vf"]    == original["vf"]
            assert processado["vp"]    == original["vp"]
            assert processado["prazo"] == original["prazo"]

    def test_campo_taxa_am_adicionado(self):
        resultado = processar_titulos(self.TITULOS)
        for t in resultado:
            assert "taxa_am" in t
            assert t["taxa_am"] > 0

    def test_taxa_am_coerente_com_calcular_taxa(self):
        resultado = processar_titulos(self.TITULOS)
        for original, processado in zip(self.TITULOS, resultado):
            esperado = calcular_taxa(original["vf"], original["vp"], original["prazo"])
            assert processado["taxa_am"] == pytest.approx(esperado, abs=TOLERANCE)

    def test_lista_vazia(self):
        assert processar_titulos([]) == []


# ─────────────────────────────────────────────
# projetar_nova_taxa
# ─────────────────────────────────────────────

class TestProjetarNovaTaxa:
    TITULOS = [
        {"vf": 63.33,  "vp": 56.36,  "prazo": 76},
        {"vf": 39.99,  "vp": 35.59,  "prazo": 76},
        {"vf": 115.96, "vp": 103.20, "prazo": 76},
        {"vf": 55.54,  "vp": 49.43,  "prazo": 91},
        {"vf": 96.00,  "vp": 85.44,  "prazo": 91},
    ]

    def test_estrutura_retorno(self):
        r = projetar_nova_taxa(self.TITULOS, 0.05)
        assert "titulos" in r
        assert "total_vp_original" in r
        assert "total_novo_vp" in r
        assert "diferenca" in r

    def test_total_vp_original_correto(self):
        r = projetar_nova_taxa(self.TITULOS, 0.05)
        esperado = sum(t["vp"] for t in self.TITULOS)
        assert r["total_vp_original"] == pytest.approx(esperado, abs=TOLERANCE)

    def test_total_novo_vp_correto(self):
        nova_taxa = 0.05
        r = projetar_nova_taxa(self.TITULOS, nova_taxa)
        esperado = sum(calcular_vp(t["vf"], nova_taxa, t["prazo"]) for t in self.TITULOS)
        assert r["total_novo_vp"] == pytest.approx(esperado, abs=TOLERANCE)

    def test_diferenca_coerente(self):
        r = projetar_nova_taxa(self.TITULOS, 0.05)
        assert r["diferenca"] == pytest.approx(r["total_novo_vp"] - r["total_vp_original"], abs=TOLERANCE)

    def test_taxa_maior_reduz_total(self):
        """Taxa mais alta → menor VP total."""
        r_baixa = projetar_nova_taxa(self.TITULOS, 0.03)
        r_alta  = projetar_nova_taxa(self.TITULOS, 0.10)
        assert r_alta["total_novo_vp"] < r_baixa["total_novo_vp"]

    def test_valores_planilha_nova_taxa_50pct(self):
        """Valida contra coluna 'Novo VP' da planilha com taxa=50% a.m."""
        titulos = [
            {"vf": 63.33,  "vp": 56.36, "prazo": 76},
            {"vf": 39.99,  "vp": 35.59, "prazo": 76},
            {"vf": 115.96, "vp": 103.20, "prazo": 76},
        ]
        novos_vp_esperados = [22.67, 14.32, 41.52]
        r = projetar_nova_taxa(titulos, 0.5)
        for titulo, esperado in zip(r["titulos"], novos_vp_esperados):
            assert titulo["novo_vp"] == pytest.approx(esperado, rel=0.01)

    def test_lista_vazia(self):
        r = projetar_nova_taxa([], 0.05)
        assert r["total_vp_original"] == 0
        assert r["total_novo_vp"] == 0
        assert r["diferenca"] == 0


# ─────────────────────────────────────────────
# taxa_equivalente_total
# ─────────────────────────────────────────────

class TestTaxaEquivalenteTotal:
    def test_titulos_mesma_taxa_retorna_essa_taxa(self):
        """Carteira homogênea deve retornar exatamente a taxa de todos."""
        taxa = 0.047
        titulos = [
            {"vf": calcular_vf(100, taxa, 76), "vp": 100.0, "prazo": 76},
            {"vf": calcular_vf(200, taxa, 76), "vp": 200.0, "prazo": 76},
            {"vf": calcular_vf(150, taxa, 76), "vp": 150.0, "prazo": 76},
        ]
        assert taxa_equivalente_total(titulos) == pytest.approx(taxa, abs=TOLERANCE)

    def test_ponderacao_pelo_vf(self):
        """Título com VF maior deve puxar a média para sua taxa."""
        titulos = [
            {"vf": 1000.0, "vp": 900.0, "prazo": 30},   # taxa ~11.1% — peso grande
            {"vf":   10.0, "vp":   9.5, "prazo": 30},   # taxa ~5.3%  — peso pequeno
        ]
        media = taxa_equivalente_total(titulos)
        taxa_grande = calcular_taxa(1000, 900, 30)
        taxa_pequena = calcular_taxa(10, 9.5, 30)
        assert taxa_grande > media > taxa_pequena


class TestConversaoTaxas:
    def test_conversao_1pct_am_para_aa(self):
        """1% a.m. deve ser ~12.68% a.a."""
        from src.classes.analise_cnab import converter_para_anual
        assert converter_para_anual(0.01) == pytest.approx(0.126825, abs=1e-5)

    def test_conversao_inversa(self):
        from src.classes.analise_cnab import converter_para_anual, converter_para_mensal
        taxa_orig = 0.05
        aa = converter_para_anual(taxa_orig)
        assert converter_para_mensal(aa) == pytest.approx(taxa_orig, abs=1e-10)
