"""
Gráfico de barras em SVG feito com Python puro (sem matplotlib/NumPy).

Usado como alternativa quando o matplotlib não carrega (ex.: NumPy incompatível
com a versão do Python). O arquivo .svg abre em qualquer navegador e pode ser
inserido no Word (Inserir > Imagens).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Sequence
from xml.sax.saxutils import escape

CORES = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]


def _fmt_n(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _fmt_s(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def _passo_redondo(maximo: float, divisoes: int = 5) -> float:
    """Escolhe um passo 'bonito' (1, 2 ou 5 × 10^k) para o eixo Y."""
    if maximo <= 0:
        return 1.0
    bruto = maximo / divisoes
    potencia = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 5, 10):
        if bruto <= m * potencia:
            return m * potencia
    return 10 * potencia


def barras_svg(caminho: str | Path, tamanhos: Sequence[int], series: Dict[str, List[float]],
               titulo: str = "Tempo de ordenação por algoritmo e quantidade de dados") -> Path:
    """
    Salva um gráfico de barras agrupadas: eixo X = tamanhos, uma barra por algoritmo.
    series: {"Quick Sort": [t_1000, t_10000, ...], ...} (tempos em segundos; None = sem valor)
    """
    L, A = 1100, 600                          # largura e altura da imagem
    esq, dir_, topo, base = 80, 30, 60, 70    # margens
    larg_util, alt_util = L - esq - dir_, A - topo - base

    valores = [v for vs in series.values() for v in vs if v is not None]
    passo = _passo_redondo(max(valores) if valores else 1.0)
    y_max = passo * math.ceil((max(valores) if valores else 1.0) / passo)

    def y(v: float) -> float:
        return topo + alt_util - (v / y_max) * alt_util

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{L}" height="{A}" '
         f'font-family="Arial, Helvetica, sans-serif">',
         f'<rect width="{L}" height="{A}" fill="white"/>',
         f'<text x="{L / 2}" y="32" font-size="20" text-anchor="middle">{escape(titulo)}</text>']

    # Grade e eixo Y
    k = 0
    while k * passo <= y_max + 1e-12:
        v = k * passo
        p.append(f'<line x1="{esq}" x2="{L - dir_}" y1="{y(v):.1f}" y2="{y(v):.1f}" '
                 f'stroke="#ddd"/>')
        p.append(f'<text x="{esq - 8}" y="{y(v) + 4:.1f}" font-size="12" '
                 f'text-anchor="end">{_fmt_s(v)}</text>')
        k += 1
    p.append(f'<text transform="translate(22,{topo + alt_util / 2}) rotate(-90)" font-size="14" '
             f'text-anchor="middle">Tempo de ordenação (s)</text>')

    # Barras
    nomes = list(series)
    grupo = larg_util / max(1, len(tamanhos))
    larg_barra = grupo * 0.8 / max(1, len(nomes))
    for i, n in enumerate(tamanhos):
        x0 = esq + i * grupo + grupo * 0.1
        for j, nome in enumerate(nomes):
            v = series[nome][i] if i < len(series[nome]) else None
            if v is None:
                continue
            x = x0 + j * larg_barra
            p.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{larg_barra:.1f}" '
                     f'height="{topo + alt_util - y(v):.1f}" fill="{CORES[j % len(CORES)]}"/>')
            p.append(f'<text x="{x + larg_barra / 2:.1f}" y="{y(v) - 5:.1f}" font-size="11" '
                     f'text-anchor="middle">{_fmt_s(v)}</text>')
        p.append(f'<text x="{esq + i * grupo + grupo / 2:.1f}" y="{topo + alt_util + 22}" '
                 f'font-size="13" text-anchor="middle">{_fmt_n(n)}</text>')

    # Eixos e rótulo X
    p.append(f'<line x1="{esq}" x2="{L - dir_}" y1="{topo + alt_util}" y2="{topo + alt_util}" '
             f'stroke="black"/>')
    p.append(f'<line x1="{esq}" x2="{esq}" y1="{topo}" y2="{topo + alt_util}" stroke="black"/>')
    p.append(f'<text x="{esq + larg_util / 2}" y="{A - 20}" font-size="14" '
             f'text-anchor="middle">Quantidade de dados</text>')

    # Legenda
    for j, nome in enumerate(nomes):
        ly = topo + 10 + j * 22
        p.append(f'<rect x="{esq + 15}" y="{ly}" width="16" height="12" '
                 f'fill="{CORES[j % len(CORES)]}"/>')
        p.append(f'<text x="{esq + 38}" y="{ly + 11}" font-size="13">{escape(nome)}</text>')

    p.append("</svg>")
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(p), encoding="utf-8")
    return caminho


def barras_texto(tamanhos: Sequence[int], series: Dict[str, List[float]], largura: int = 50) -> str:
    """Gráfico de barras no próprio terminal (caracteres '█')."""
    valores = [v for vs in series.values() for v in vs if v is not None]
    maximo = max(valores) if valores else 1.0
    nome_max = max(len(n) for n in series)
    linhas = []
    for i, n in enumerate(tamanhos):
        linhas.append(f"n = {_fmt_n(n)}")
        for nome, vs in series.items():
            v = vs[i] if i < len(vs) else None
            if v is None:
                continue
            barra = "█" * max(1, round(v / maximo * largura))
            linhas.append(f"  {nome.ljust(nome_max)} {barra} {_fmt_s(v)} s")
    return "\n".join(linhas)
