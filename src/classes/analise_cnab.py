"""
Projeção de Taxa - Moovpay
Fórmula base: juros compostos com prazo em dias, taxa em meses (30 dias)
"""
 
 
# ─────────────────────────────────────────────
# FUNÇÕES BASE (linha a linha)
# ─────────────────────────────────────────────
 
def calcular_taxa(vf: float, vp: float, prazo: int) -> float:
    """
    Calcula a taxa mensal implícita entre VP (aquisição) e VF (nominal).
 
    Args:
        vf: Valor Futuro (nominal)
        vp: Valor Presente (aquisição)
        prazo: Prazo em dias
 
    Returns:
        Taxa mensal (ex: 0.047 = 4.7% a.m.)
    """
    if vp <= 0 or prazo <= 0:
        return 0.0
    return (vf / vp) ** (30 / prazo) - 1
 
 
def calcular_vp(vf: float, taxa: float, prazo: int) -> float:
    """
    Dado um VF e uma taxa desejada, calcula o VP (quanto pagar hoje).
 
    Args:
        vf: Valor Futuro (nominal)
        taxa: Taxa mensal desejada (ex: 0.05 = 5% a.m.)
        prazo: Prazo em dias
 
    Returns:
        Valor Presente
    """
    prazo_ajustado = max(prazo, 1)
    return vf / (1 + taxa) ** (prazo_ajustado / 30)
 
 
def calcular_vf(vp: float, taxa: float, prazo: int) -> float:
    """
    Dado um VP e uma taxa, projeta o VF (valor futuro esperado).
 
    Args:
        vp: Valor Presente
        taxa: Taxa mensal (ex: 0.05 = 5% a.m.)
        prazo: Prazo em dias
 
    Returns:
        Valor Futuro projetado
    """
    prazo_ajustado = max(prazo, 1)
    return vp * (1 + taxa) ** (prazo_ajustado / 30)
 
 
def converter_para_anual(taxa_mensal: float) -> float:
    """Converte uma taxa mensal composta para anual."""
    return (1 + taxa_mensal) ** 12 - 1
 
 
def converter_para_mensal(taxa_anual: float) -> float:
    """Converte uma taxa anual composta para mensal."""
    return (1 + taxa_anual) ** (1 / 12) - 1
 
 
# ─────────────────────────────────────────────
# FUNÇÕES PARA LOTE (lista de títulos)
# ─────────────────────────────────────────────
 
def processar_titulos(titulos: list[dict]) -> list[dict]:
    """
    Processa uma lista de títulos calculando a taxa implícita de cada um.
 
    Cada título deve ter: {'vf': float, 'vp': float, 'prazo': int}
 
    Returns:
        Lista com os dados originais + 'taxa_am' em cada item
    """
    resultado = []
    for t in titulos:
        taxa = calcular_taxa(t["vf"], t["vp"], t["prazo"])
        resultado.append({**t, "taxa_am": taxa})
    return resultado
 
 
def projetar_nova_taxa(titulos: list[dict], nova_taxa: float) -> dict:
    """
    Aplica uma nova taxa a todos os títulos e retorna os novos VPs + totais.
 
    Args:
        titulos: lista de dicts com 'vf', 'vp', 'prazo'
        nova_taxa: nova taxa mensal desejada (ex: 0.05 = 5% a.m.)
 
    Returns:
        dict com:
          - 'titulos': lista linha a linha com novo_vp
          - 'total_vp_original': soma dos VPs originais
          - 'total_novo_vp': soma dos novos VPs
          - 'diferenca': quanto muda no total
    """
    resultado = []
    total_vp_original = 0
    total_novo_vp = 0
 
    for t in titulos:
        novo_vp = calcular_vp(t["vf"], nova_taxa, t["prazo"])
        total_vp_original += t["vp"]
        total_novo_vp += novo_vp
        resultado.append({**t, "novo_vp": novo_vp})
 
    return {
        "titulos": resultado,
        "total_vp_original": total_vp_original,
        "total_novo_vp": total_novo_vp,
        "diferenca": total_novo_vp - total_vp_original,
    }
 
 
def taxa_equivalente_total(titulos: list[dict], iteracoes: int = 20) -> float:
    """
    Calcula a Taxa de Equilíbrio (Breakeven) da carteira.
    Encontra a taxa única que iguala o total de VP projetado ao total de VP original.
    
    Usa o método da bisseção para encontrar a raiz.
    """
    if not titulos:
        return 0.0

    total_vp_alvo = sum(t["vp"] for t in titulos)
    if total_vp_alvo <= 0:
        return 0.0

    # Função que calcula a diferença de VP para uma dada taxa
    def calcular_erro(taxa_teste):
        total_teste = sum(calcular_vp(t["vf"], taxa_teste, t["prazo"]) for t in titulos)
        return total_teste - total_vp_alvo

    # Busca binária (Bisseção) entre 0% e 100% a.m.
    low = 0.0
    high = 1.0  # 100% a.m. (limite razoável para busca)
    
    # Se a 0% o VP já é menor que o alvo, algo está errado (VP original > VF total)
    if calcular_erro(low) < 0:
        # Tenta uma média simples como fallback caso os dados estejam inconsistentes
        soma_vf = sum(t["vf"] for t in titulos)
        return sum(calcular_taxa(t["vf"], t["vp"], t["prazo"]) * (t["vf"] / soma_vf) for t in titulos)

    for _ in range(iteracoes):
        mid = (low + high) / 2
        erro = calcular_erro(mid)
        
        if abs(erro) < 0.01: # Precisão de 1 centavo
            return mid
        
        if erro > 0:
            low = mid
        else:
            high = mid
            
    return (low + high) / 2
 