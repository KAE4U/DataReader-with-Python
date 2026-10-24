"""
Implementações dos algoritmos de ordenação.

Foram mantidos os 3 algoritmos de MELHOR DESEMPENHO na bateria completa de testes
(tempo médio com n = 100.000 números aleatórios):
    1º Quick Sort   O(n log n)   não estável  (mediana de três + Hoare, iterativo)
    2º Merge Sort   O(n log n)   estável
    3º Shell Sort   ~O(n^1.3)    não estável  (sequência de Ciura)

Convenções:
    * Todas as funções ordenam a lista IN-PLACE, em ordem crescente, e retornam None.
    * Nenhuma função usa list.sort()/sorted() internamente.
    * Implementações iterativas foram preferidas onde a recursão poderia estourar
      o limite de pilha do Python (ex.: Quick Sort em dados já ordenados).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


# ===========================================================================
# 1. SHELL SORT (sequência de lacunas de Ciura, 2001)
# ===========================================================================
_GAPS_CIURA = (1, 4, 10, 23, 57, 132, 301, 701, 1750)


def _lacunas(n: int) -> List[int]:
    """Gera as lacunas (gaps) em ordem decrescente, estendendo Ciura por ×2,25."""
    gaps = list(_GAPS_CIURA)
    while gaps[-1] < n:
        gaps.append(int(gaps[-1] * 2.25))
    return [g for g in reversed(gaps) if g < n]


def shell_sort(v: List[int]) -> None:
    """
    Generalização do Insertion Sort: ordena subsequências de elementos
    distantes 'gap' posições, reduzindo o gap até 1. Movimentos longos
    iniciais eliminam rapidamente grande parte das inversões.
    """
    n = len(v)
    for gap in _lacunas(n):
        for i in range(gap, n):
            temp = v[i]
            j = i
            while j >= gap and v[j - gap] > temp:
                v[j] = v[j - gap]
                j -= gap
            v[j] = temp


# ===========================================================================
# 2. MERGE SORT (top-down, buffer auxiliar único)
# ===========================================================================
def merge_sort(v: List[int]) -> None:
    """
    Divisão e conquista: divide o vetor ao meio, ordena cada metade
    recursivamente e intercala (merge) as duas metades ordenadas.
    Usa um único vetor auxiliar (O(n) de memória) alocado uma vez.
    A profundidade de recursão é log2(n) (~17 para 100.000), segura em Python.
    """
    if len(v) < 2:
        return
    aux = v[:]  # buffer auxiliar
    _merge_sort_rec(v, aux, 0, len(v))


def _merge_sort_rec(v: List[int], aux: List[int], ini: int, fim: int) -> None:
    """Ordena o intervalo semiaberto v[ini:fim]."""
    if fim - ini < 2:
        return
    meio = (ini + fim) // 2
    _merge_sort_rec(v, aux, ini, meio)
    _merge_sort_rec(v, aux, meio, fim)

    # Otimização (Sedgewick): se as metades já estão em ordem, não intercala.
    if v[meio - 1] <= v[meio]:
        return

    aux[ini:fim] = v[ini:fim]
    i, j, k = ini, meio, ini
    while i < meio and j < fim:
        if aux[i] <= aux[j]:          # '<=' garante estabilidade
            v[k] = aux[i]
            i += 1
        else:
            v[k] = aux[j]
            j += 1
        k += 1
    # Resto da metade esquerda (o resto da direita já está na posição certa)
    if i < meio:
        v[k:k + (meio - i)] = aux[i:meio]


# ===========================================================================
# 3. QUICK SORT (iterativo, mediana de três, partição de Hoare)
# ===========================================================================
def quick_sort(v: List[int]) -> None:
    """
    Escolhe um pivô, particiona o vetor em (<= pivô) e (>= pivô) e repete
    em cada parte.

    Decisões de engenharia:
      * Pivô pela MEDIANA DE TRÊS (início, meio, fim): evita o pior caso O(n²)
        em vetores já ordenados ou invertidos.
      * Partição de HOARE: lida bem com muitos valores repetidos (há apenas
        100.000 valores possíveis no domínio 0..99.999).
      * Pilha EXPLÍCITA (sem recursão) e processamento da menor partição
        primeiro: pilha limitada a O(log n), sem RecursionError.
    """
    if len(v) < 2:
        return
    pilha = [(0, len(v) - 1)]
    while pilha:
        ini, fim = pilha.pop()
        while ini < fim:
            p = _particao_hoare(v, ini, fim)
            # Empilha a maior parte e continua (laço) com a menor
            if p - ini < fim - p:
                pilha.append((p + 1, fim))
                fim = p
            else:
                pilha.append((ini, p))
                ini = p + 1


def _particao_hoare(v: List[int], ini: int, fim: int) -> int:
    """Particiona v[ini..fim]; retorna j tal que v[ini..j] <= v[j+1..fim]."""
    meio = (ini + fim) // 2
    # Mediana de três: ordena v[ini], v[meio], v[fim]
    if v[meio] < v[ini]:
        v[ini], v[meio] = v[meio], v[ini]
    if v[fim] < v[ini]:
        v[ini], v[fim] = v[fim], v[ini]
    if v[fim] < v[meio]:
        v[meio], v[fim] = v[fim], v[meio]
    pivo = v[meio]

    i, j = ini - 1, fim + 1
    while True:
        i += 1
        while v[i] < pivo:
            i += 1
        j -= 1
        while v[j] > pivo:
            j -= 1
        if i >= j:
            return j
        v[i], v[j] = v[j], v[i]


# ===========================================================================
# Registro dos algoritmos + metadados (usados em tabelas, gráficos e menu)
# ===========================================================================
@dataclass(frozen=True)
class Algoritmo:
    chave: str
    nome: str
    funcao: Callable[[List[int]], None]
    melhor: str
    medio: str
    pior: str
    memoria: str
    estavel: bool


ALGORITMOS = {
    a.chave: a
    for a in (
        Algoritmo("shell", "Shell Sort", shell_sort, "O(n log n)", "~O(n^1,3)", "~O(n^1,5)", "O(1)", False),
        Algoritmo("merge", "Merge Sort", merge_sort, "O(n)*", "O(n log n)", "O(n log n)", "O(n)", True),
        Algoritmo("quick", "Quick Sort", quick_sort, "O(n log n)", "O(n log n)", "O(n²)**", "O(log n)", False),
    )
}
# *  Com a verificação 'v[meio-1] <= v[meio]' o Merge Sort é linear em dados já ordenados.
# ** Pior caso raríssimo com mediana de três; não ocorre nos cenários testados.

ORDEM_ALGORITMOS = list(ALGORITMOS.keys())


def obter(chave: str) -> Algoritmo:
    """Retorna o algoritmo pela chave, com mensagem clara caso não exista."""
    try:
        return ALGORITMOS[chave]
    except KeyError:
        validos = ", ".join(ALGORITMOS)
        raise ValueError(f"Algoritmo '{chave}' desconhecido. Válidos: {validos}") from None
