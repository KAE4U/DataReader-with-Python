"""
Geração de gráficos (matplotlib) a partir dos resultados.

Gera um único gráfico de barras (escala linear): Quantidade de dados x Tempo de
ordenação, com uma barra por algoritmo (grafico_barras.png, ou .svg sem matplotlib).
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from . import algoritmos, config, grafico_svg
from .benchmark import OK, ResultadoTeste

try:
    import matplotlib
    matplotlib.use("Agg")                 # renderiza em arquivo, sem janela
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
    MATPLOTLIB_ERRO = ""
except Exception as _e:                   # ImportError, ou SystemError de NumPy incompatível
    MATPLOTLIB_OK = False
    MATPLOTLIB_ERRO = f"{type(_e).__name__}: {_e}"

TITULO = "Tempo de ordenação por algoritmo e quantidade de dados"


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
    if not any(r.status == OK for r in resultados):
        return []
    pasta = Path(pasta)
    series = _series(resultados)
    chaves = _chaves_presentes(resultados)
    cenarios = [c for c in config.CENARIOS if any(k[0] == c for k in series)]
    arquivos = []

    if not MATPLOTLIB_OK:
        # Alternativa sem dependências: gráfico de barras em SVG (Python puro)
        print(f"[AVISO] matplotlib indisponível ({MATPLOTLIB_ERRO}).\n"
              f"        Python em uso: {sys.executable}\n"
              f"        Para PNG, instale nele: \"{sys.executable}\" -m pip install -r requirements.txt\n"
              f"        Gerando gráfico de barras em SVG (sem dependências)...")
        for cen in cenarios:
            tamanhos = sorted({n for (c, _), pts in series.items() if c == cen for n, _ in pts})
            dados_svg = {}
            for ch in chaves:
                mapa = dict(series.get((cen, ch), []))
                dados_svg[algoritmos.obter(ch).nome] = [mapa.get(n) for n in tamanhos]
            arquivos.append(grafico_svg.barras_svg(
                pasta / "grafico_barras.svg", tamanhos, dados_svg, TITULO))
        return arquivos

    # Gráfico de barras: Quantidade de dados x Tempo de ordenação (escala linear)
    for cen in cenarios:
        tamanhos = sorted({n for (c, _), pts in series.items() if c == cen for n, _ in pts})
        presentes = [ch for ch in chaves if series.get((cen, ch))]
        largura = 0.8 / max(1, len(presentes))
        fig, ax = plt.subplots(figsize=(11, 6))
        for i, ch in enumerate(presentes):
            mapa = dict(series[(cen, ch)])
            xs = [j + i * largura for j in range(len(tamanhos))]
            ys = [mapa.get(n, 0) for n in tamanhos]
            barras = ax.bar(xs, ys, width=largura, label=algoritmos.obter(ch).nome)
            ax.bar_label(barras, labels=[f"{t:.3f}".replace(".", ",") for t in ys],
                         fontsize=7, padding=2)
        ax.set_xticks([j + largura * (len(presentes) - 1) / 2 for j in range(len(tamanhos))])
        ax.set_xticklabels([config.fmt_int(n) for n in tamanhos])
        ax.set_xlabel("Quantidade de dados")
        ax.set_ylabel("Tempo de ordenação (s)")
        ax.set_title(TITULO)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend()
        arquivos.append(_salvar(fig, pasta / "grafico_barras.png"))

    return arquivos
