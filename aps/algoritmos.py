"""
Implementações dos algoritmos de ordenação.

Convenções:
    * Todas as funções ordenam a lista IN-PLACE, em ordem crescente, e retornam None.
    * Nenhuma função usa list.sort()/sorted() internamente (exceto a referência Timsort).
    * Implementações iterativas foram preferidas onde a recursão poderia estourar
      o limite de pilha do Python (ex.: Quick Sort em dados já ordenados).

Algoritmos (do mais lento ao mais rápido, em média):
    Bubble Sort     O(n²)        estável
    Insertion Sort  O(n²)        estável
    Shell Sort      ~O(n^1.3)    não estável  (sequência de Ciura)
    Heap Sort       O(n log n)   não estável
    Merge Sort      O(n log n)   estável
    Quick Sort      O(n log n)   não estável  (mediana de três + Hoare, iterativo)
    Timsort nativo  O(n log n)   estável      (referência: list.sort() em C)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


# ===========================================================================
# 1. BUBBLE SORT (otimizado)
# ===========================================================================
def bubble_sort(v: List[int]) -> None:
    """
    Compara pares adjacentes e os troca quando fora de ordem; a cada passagem
    o maior elemento restante "flutua" para o final.

    Otimizações clássicas:
      * guarda a posição da última troca: tudo depois dela já está ordenado,
        então a próxima passagem pode parar ali;
      * se nenhuma troca ocorrer, o vetor está ordenado (melhor caso O(n)).
    """
    limite = len(v) - 1
    while limite > 0:
        ultima_troca = 0
        for i in range(limite):
            if v[i] > v[i + 1]:
                v[i], v[i + 1] = v[i + 1], v[i]
                ultima_troca = i
        limite = ultima_troca  # 0 => nenhuma troca => fim


# ===========================================================================
# 2. INSERTION SORT
# ===========================================================================
def insertion_sort(v: List[int]) -> None:
    """
    Mantém o prefixo v[0..i-1] ordenado e insere v[i] na posição correta,
    deslocando para a direita os elementos maiores (como ordenar cartas na mão).
    Muito eficiente para vetores pequenos ou quase ordenados (adaptativo).
    """
    for i in range(1, len(v)):
        chave = v[i]
        j = i - 1
        while j >= 0 and v[j] > chave:
            v[j + 1] = v[j]
            j -= 1
        v[j + 1] = chave


# ===========================================================================
# 3. SHELL SORT (sequência de lacunas de Ciura, 2001)
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
# 4. MERGE SORT (top-down, buffer auxiliar único)
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
# 5. HEAP SORT
# ===========================================================================
def heap_sort(v: List[int]) -> None:
    """
    1) Constrói um max-heap no próprio vetor (O(n)).
    2) Repetidamente troca a raiz (maior) com o último elemento do heap,
       reduz o heap e restaura a propriedade com 'sift-down' (O(log n)).
    Garantia O(n log n) em todos os casos e memória O(1).
    """
    n = len(v)
    for i in range(n // 2 - 1, -1, -1):
        _sift_down(v, i, n)
    for fim in range(n - 1, 0, -1):
        v[0], v[fim] = v[fim], v[0]
        _sift_down(v, 0, fim)


def _sift_down(v: List[int], i: int, n: int) -> None:
    """Desce v[i] no heap v[0:n] até que seja maior que seus filhos."""
    valor = v[i]
    while True:
        filho = 2 * i + 1
        if filho >= n:
            break
        if filho + 1 < n and v[filho + 1] > v[filho]:
            filho += 1
        if v[filho] <= valor:
            break
        v[i] = v[filho]   # sobe o filho (evita trocas completas)
        i = filho
    v[i] = valor


# ===========================================================================
# 6. QUICK SORT (iterativo, mediana de três, partição de Hoare)
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
# 7. REFERÊNCIA: Timsort nativo do Python (implementado em C)
# ===========================================================================
def timsort_nativo(v: List[int]) -> None:
    """Linha de base: list.sort() (Timsort, em C). Não é implementação do grupo."""
    v.sort()


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
    referencia: bool = False   # True = não é implementação própria


ALGORITMOS = {
    a.chave: a
    for a in (
        Algoritmo("bubble", "Bubble Sort", bubble_sort, "O(n)", "O(n²)", "O(n²)", "O(1)", True),
        Algoritmo("insertion", "Insertion Sort", insertion_sort, "O(n)", "O(n²)", "O(n²)", "O(1)", True),
        Algoritmo("shell", "Shell Sort", shell_sort, "O(n log n)", "~O(n^1,3)", "~O(n^1,5)", "O(1)", False),
        Algoritmo("heap", "Heap Sort", heap_sort, "O(n log n)", "O(n log n)", "O(n log n)", "O(1)", False),
        Algoritmo("merge", "Merge Sort", merge_sort, "O(n)*", "O(n log n)", "O(n log n)", "O(n)", True),
        Algoritmo("quick", "Quick Sort", quick_sort, "O(n log n)", "O(n log n)", "O(n²)**", "O(log n)", False),
        Algoritmo("timsort", "Timsort nativo (ref.)", timsort_nativo, "O(n)", "O(n log n)", "O(n log n)", "O(n)", True, True),
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
