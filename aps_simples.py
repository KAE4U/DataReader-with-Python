"""
APS - Estruturas de Dados (UNIP) - versão simples.
Roda 4 algoritmos de ordenação com 1.000, 10.000, 50.000, 80.000 e 100.000
números aleatórios (0 a 99.999), mostra o tempo de cada um e gera um gráfico de barras.

Uso:  python aps_simples.py
"""

import csv
import random
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TAMANHOS = [1_000, 10_000, 50_000, 80_000, 100_000]


# ---------------------------- Algoritmos ----------------------------------
def insertion_sort(v):
    for i in range(1, len(v)):
        chave = v[i]
        j = i - 1
        while j >= 0 and v[j] > chave:
            v[j + 1] = v[j]
            j -= 1
        v[j + 1] = chave


def merge_sort(v):
    if len(v) <= 1:
        return v
    meio = len(v) // 2
    esq, dir_ = merge_sort(v[:meio]), merge_sort(v[meio:])
    res, i, j = [], 0, 0
    while i < len(esq) and j < len(dir_):
        if esq[i] <= dir_[j]:
            res.append(esq[i]); i += 1
        else:
            res.append(dir_[j]); j += 1
    res.extend(esq[i:]); res.extend(dir_[j:])
    v[:] = res          # ordena a lista original
    return v


def heap_sort(v):
    def descer(i, n):
        while True:
            maior, e, d = i, 2 * i + 1, 2 * i + 2
            if e < n and v[e] > v[maior]: maior = e
            if d < n and v[d] > v[maior]: maior = d
            if maior == i: return
            v[i], v[maior] = v[maior], v[i]
            i = maior
    n = len(v)
    for i in range(n // 2 - 1, -1, -1):
        descer(i, n)
    for fim in range(n - 1, 0, -1):
        v[0], v[fim] = v[fim], v[0]
        descer(0, fim)


def quick_sort(v):
    pilha = [(0, len(v) - 1)]          # iterativo: sem estouro de recursão
    while pilha:
        ini, fim = pilha.pop()
        if ini >= fim:
            continue
        pivo = v[(ini + fim) // 2]
        i, j = ini, fim
        while i <= j:
            while v[i] < pivo: i += 1
            while v[j] > pivo: j -= 1
            if i <= j:
                v[i], v[j] = v[j], v[i]
                i += 1; j -= 1
        pilha.append((ini, j))
        pilha.append((i, fim))


ALGORITMOS = {
    "Insertion Sort": insertion_sort,
    "Merge Sort": merge_sort,
    "Heap Sort": heap_sort,
    "Quick Sort": quick_sort,
}


# ---------------------------- Execução ------------------------------------
def main():
    random.seed(2026)
    resultados = {nome: [] for nome in ALGORITMOS}

    for n in TAMANHOS:
        dados = [random.randint(0, 99_999) for _ in range(n)]   # geração (não cronometrada)
        for nome, funcao in ALGORITMOS.items():
            copia = dados.copy()
            inicio = time.perf_counter()                        # só a ordenação é medida
            funcao(copia)
            tempo = time.perf_counter() - inicio
            assert copia == sorted(dados), f"{nome} ordenou errado"
            resultados[nome].append(tempo)
            print(f"{nome:<15} n={n:>7,}  ->  {tempo:.4f} s".replace(",", "."))

    # Tabela
    print("\n" + "Algoritmo".ljust(16) + "".join(f"{n:>12,}".replace(",", ".") for n in TAMANHOS))
    for nome, tempos in resultados.items():
        print(nome.ljust(16) + "".join(f"{t:>11.4f}s" for t in tempos))

    # CSV
    with open("resultados_simples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["algoritmo"] + TAMANHOS)
        for nome, tempos in resultados.items():
            w.writerow([nome] + [f"{t:.6f}".replace(".", ",") for t in tempos])

    # Gráfico de barras: Tamanho x Tempo
    largura = 0.2
    fig, ax = plt.subplots(figsize=(11, 6))
    for k, (nome, tempos) in enumerate(resultados.items()):
        xs = [i + k * largura for i in range(len(TAMANHOS))]
        ax.bar(xs, tempos, width=largura, label=nome)
    ax.set_xticks([i + 1.5 * largura for i in range(len(TAMANHOS))])
    ax.set_xticklabels([f"{n:,}".replace(",", ".") for n in TAMANHOS])
    ax.set_yscale("log")   # escala log: Insertion é milhares de vezes mais lento
    ax.set_xlabel("Quantidade de dados")
    ax.set_ylabel("Tempo de ordenação (s) - escala log")
    ax.set_title("Tempo de ordenação por algoritmo e quantidade de dados")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig("grafico_barras.png", dpi=150)
    print("\nSalvo: resultados_simples.csv e grafico_barras.png")


if __name__ == "__main__":
    main()
