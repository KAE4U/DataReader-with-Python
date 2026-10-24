"""
APS - Estruturas de Dados (UNIP) - versão simples.
Roda os 3 algoritmos de ordenação mais rápidos (Quick Sort, Merge Sort e Shell Sort)
com 1.000, 10.000, 50.000, 80.000 e 100.000 números aleatórios (0 a 99.999),
mostra o tempo de cada um e gera um gráfico de barras.

Uso:  python aps_simples.py
"""

import csv
import random
import sys
import time

from aps import grafico_svg   # gráfico de barras sem matplotlib (SVG e terminal)

TAMANHOS = [1_000, 10_000, 50_000, 80_000, 100_000]


# ---------------------------- Algoritmos ----------------------------------
def quick_sort(v):
    """Quick Sort iterativo com pivô no meio (sem estouro de recursão)."""
    pilha = [(0, len(v) - 1)]
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


def merge_sort(v):
    """Merge Sort: divide ao meio, ordena cada metade e intercala."""
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


def shell_sort(v):
    """Shell Sort com a sequência de lacunas de Ciura (estendida por ×2,25)."""
    n = len(v)
    gaps = [1, 4, 10, 23, 57, 132, 301, 701, 1750]
    while gaps[-1] < n:
        gaps.append(int(gaps[-1] * 2.25))
    for gap in reversed(gaps):
        for i in range(gap, n):
            temp = v[i]
            j = i
            while j >= gap and v[j - gap] > temp:
                v[j] = v[j - gap]
                j -= gap
            v[j] = temp


ALGORITMOS = {
    "Quick Sort": quick_sort,
    "Merge Sort": merge_sort,
    "Shell Sort": shell_sort,
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
            print(f"{nome:<12} n={n:>7,}  ->  {tempo:.4f} s".replace(",", "."))

    # Tabela
    print("\n" + "Algoritmo".ljust(13) + "".join(f"{n:>12,}".replace(",", ".") for n in TAMANHOS))
    for nome, tempos in resultados.items():
        print(nome.ljust(13) + "".join(f"{t:>11.4f}s" for t in tempos))

    # CSV
    with open("resultados_simples.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["algoritmo"] + TAMANHOS)
        for nome, tempos in resultados.items():
            w.writerow([nome] + [f"{t:.6f}".replace(".", ",") for t in tempos])

    print("\nSalvo: resultados_simples.csv")

    # Gráfico de barras no próprio terminal (não depende de nenhuma biblioteca)
    print("\nGráfico de barras (tempo em segundos):")
    print(grafico_svg.barras_texto(TAMANHOS, resultados))

    # Gráfico de barras em imagem: Tamanho x Tempo
    # (matplotlib é importado só aqui; se falhar, gera o gráfico em SVG com Python puro)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:  # ImportError ou SystemError (NumPy incompatível com o Python)
        print(f"\n[AVISO] matplotlib indisponível ({type(e).__name__}: {e}).")
        print(f"        Python em uso: {sys.executable}")
        print(f"        Para PNG, instale nele: \"{sys.executable}\" -m pip install -r requirements.txt")
        print("        Gerando o gráfico em SVG sem dependências...")
        grafico_svg.barras_svg("grafico_barras.svg", TAMANHOS, resultados)
        print("Salvo: grafico_barras.svg  (abra no navegador ou insira no Word)")
        return

    largura = 0.25
    fig, ax = plt.subplots(figsize=(11, 6))
    for k, (nome, tempos) in enumerate(resultados.items()):
        xs = [i + k * largura for i in range(len(TAMANHOS))]
        barras = ax.bar(xs, tempos, width=largura, label=nome)
        ax.bar_label(barras, labels=[f"{t:.3f}".replace(".", ",") for t in tempos],
                     fontsize=7, padding=2)
    ax.set_xticks([i + largura for i in range(len(TAMANHOS))])
    ax.set_xticklabels([f"{n:,}".replace(",", ".") for n in TAMANHOS])
    ax.set_xlabel("Quantidade de dados")
    ax.set_ylabel("Tempo de ordenação (s)")
    ax.set_title("Tempo de ordenação por algoritmo e quantidade de dados")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig("grafico_barras.png", dpi=150)
    print("Salvo: grafico_barras.png")


if __name__ == "__main__":
    main()
