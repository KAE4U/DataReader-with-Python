"""
Geração de gráficos (matplotlib) a partir dos resultados.

Gráficos gerados:
  1. linha_<cenario>.png      Tamanho do vetor x Tempo (escala linear e logarítmica)
  2. barras_<cenario>.png     Barras agrupadas por tamanho, uma barra por algoritmo
  3. comparativo_cenarios.png Algoritmo x Cenário no maior tamanho medido
  4. linha_<algoritmo>.png    Um gráfico por algoritmo comparando os 4 cenários
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from . import algoritmos, config
from .benchmark import OK, ResultadoTeste

try:
    import matplotlib
    matplotlib.use("Agg")                 # renderiza em arquivo, sem janela
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    MATPLOTLIB_OK = True
    MATPLOTLIB_ERRO = ""
except Exception as _e:                   # ImportError, ou SystemError de NumPy incompatível
    MATPLOTLIB_OK = False
    MATPLOTLIB_ERRO = f"{type(_e).__name__}: {_e}"

_MARCADORES = ["o", "s", "^", "D", "v", "P", "X"]


def _fmt_eixo_n():
    return FuncFormatter(lambda x, _p: config.fmt_int(int(x)))


def _series(resultados: List[ResultadoTeste]) -> Dict[Tuple[str, str], List[Tuple[int, float]]]:
    """(cenario, chave) -> [(n, tempo_medio)] apenas para testes concluídos."""
    s = defaultdict(list)
    for r in resultados:
        if r.status == OK and r.tempo_medio is not None:
            s[(r.cenario, r.chave)].append((r.tamanho, r.tempo_medio))
    for k in s:
        s[k].sort()
    return s


def _chaves_presentes(resultados) -> List[str]:
    presentes = {r.chave for r in resultados}
    return [c for c in algoritmos.ORDEM_ALGORITMOS if c in presentes]


def _salvar(fig, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    return destino


def gerar_todos(resultados: List[ResultadoTeste], pasta: Path = config.DIR_GRAFICOS,
                subtitulo: str = "") -> List[Path]:
    """Gera todos os gráficos e retorna a lista de arquivos criados."""
    if not MATPLOTLIB_OK:
        raise RuntimeError(f"Gráficos desativados: não foi possível carregar o matplotlib "
                           f"({MATPLOTLIB_ERRO}). Use Python 3.12/3.13 e rode "
                           f"'pip install -r requirements.txt'.")
    if not any(r.status == OK for r in resultados):
        return []
    pasta = Path(pasta)
    series = _series(resultados)
    chaves = _chaves_presentes(resultados)
    cenarios = [c for c in config.CENARIOS if any(k[0] == c for k in series)]
    arquivos = []

    # 1) Linhas: Tamanho x Tempo por cenário (linear + log)
    for cen in cenarios:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))
        for i, ch in enumerate(chaves):
            pts = series.get((cen, ch))
            if not pts:
                continue
            xs, ys = zip(*pts)
            for ax in (ax1, ax2):
                ax.plot(xs, ys, marker=_MARCADORES[i % len(_MARCADORES)],
                        label=algoritmos.obter(ch).nome, linewidth=1.8)
        for ax, titulo in ((ax1, "Escala linear"), (ax2, "Escala logarítmica")):
            ax.set_title(titulo)
            ax.set_xlabel("Tamanho do vetor (n)")
            ax.set_ylabel("Tempo de ordenação (s)")
            ax.xaxis.set_major_formatter(_fmt_eixo_n())
            ax.grid(True, alpha=0.3)
        ax2.set_yscale("log")
        ax1.legend(fontsize=8)
        fig.suptitle(f"Tamanho x Tempo - Cenário: {config.NOMES_CENARIOS[cen]}"
                     + (f"\n{subtitulo}" if subtitulo else ""), fontsize=11)
        arquivos.append(_salvar(fig, pasta / f"linha_{cen}.png"))

    # 2) Barras agrupadas por tamanho
    for cen in cenarios:
        tamanhos = sorted({n for (c, _), pts in series.items() if c == cen for n, _ in pts})
        presentes = [ch for ch in chaves if series.get((cen, ch))]
        largura = 0.8 / max(1, len(presentes))
        fig, ax = plt.subplots(figsize=(12, 5.5))
        for i, ch in enumerate(presentes):
            mapa = dict(series[(cen, ch)])
            xs = [j + i * largura for j in range(len(tamanhos))]
            ys = [mapa.get(n, 0) for n in tamanhos]
            ax.bar(xs, ys, width=largura, label=algoritmos.obter(ch).nome)
        ax.set_xticks([j + largura * (len(presentes) - 1) / 2 for j in range(len(tamanhos))])
        ax.set_xticklabels([config.fmt_int(n) for n in tamanhos])
        ax.set_yscale("log")
        ax.set_xlabel("Tamanho do vetor (n)")
        ax.set_ylabel("Tempo de ordenação (s) - escala log")
        ax.set_title(f"Comparativo por tamanho - {config.NOMES_CENARIOS[cen]}"
                     + (f"\n{subtitulo}" if subtitulo else ""), fontsize=11)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(fontsize=8)
        arquivos.append(_salvar(fig, pasta / f"barras_{cen}.png"))

    # 3) Algoritmo x Cenário no maior n medido (barra ausente = timeout/ignorado)
    validos = [r for r in resultados if r.status == OK]
    n_max = max(r.tamanho for r in validos)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    largura = 0.8 / max(1, len(cenarios))
    for i, cen in enumerate(cenarios):
        ys = []
        for ch in chaves:
            mapa = dict(series.get((cen, ch), []))
            ys.append(mapa.get(n_max, 0))
        ax.bar([j + i * largura for j in range(len(chaves))], ys, width=largura,
               label=config.NOMES_CENARIOS[cen])
    ax.set_xticks([j + largura * (len(cenarios) - 1) / 2 for j in range(len(chaves))])
    ax.set_xticklabels([algoritmos.obter(c).nome for c in chaves], rotation=15)
    ax.set_yscale("log")
    ax.set_ylabel("Tempo de ordenação (s) - escala log")
    ax.set_title(f"Influência da disposição dos dados (n={config.fmt_int(n_max)})"
                 + "  |  barra ausente = excedeu o tempo limite"
                 + (f"\n{subtitulo}" if subtitulo else ""), fontsize=11)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    arquivos.append(_salvar(fig, pasta / "comparativo_cenarios.png"))

    # 4) Um gráfico por algoritmo (4 cenários)
    for ch in chaves:
        fig, ax = plt.subplots(figsize=(8, 5))
        tem = False
        for i, cen in enumerate(cenarios):
            pts = series.get((cen, ch))
            if pts:
                tem = True
                xs, ys = zip(*pts)
                ax.plot(xs, ys, marker=_MARCADORES[i % len(_MARCADORES)],
                        label=config.NOMES_CENARIOS[cen])
        if not tem:
            plt.close(fig)
            continue
        ax.set_title(f"{algoritmos.obter(ch).nome} - Tamanho x Tempo por cenário"
                     + (f"\n{subtitulo}" if subtitulo else ""), fontsize=11)
        ax.set_xlabel("Tamanho do vetor (n)")
        ax.set_ylabel("Tempo de ordenação (s)")
        ax.xaxis.set_major_formatter(_fmt_eixo_n())
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        arquivos.append(_salvar(fig, pasta / f"algoritmo_{ch}.png"))

    return arquivos
