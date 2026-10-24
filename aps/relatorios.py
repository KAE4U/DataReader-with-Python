"""Tabelas comparativas em texto (console e arquivo), sem dependências externas."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import algoritmos, config
from .benchmark import OK, TIMEOUT, IGNORADO, ResultadoTeste


def _tabela(cabecalho: Sequence[str], linhas: List[Sequence[str]],
            alinhar_esq: int = 1) -> str:
    """Monta uma tabela ASCII. As 'alinhar_esq' primeiras colunas ficam à esquerda."""
    larguras = [len(c) for c in cabecalho]
    for ln in linhas:
        for i, cel in enumerate(ln):
            larguras[i] = max(larguras[i], len(cel))

    def fmt(ln):
        cels = [(c.ljust(larguras[i]) if i < alinhar_esq else c.rjust(larguras[i]))
                for i, c in enumerate(ln)]
        return "| " + " | ".join(cels) + " |"

    sep = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"
    return "\n".join([sep, fmt(cabecalho), sep, *map(fmt, linhas), sep])


def _celula(r: Optional[ResultadoTeste]) -> str:
    if r is None:
        return "-"
    if r.status == OK:
        return config.fmt_tempo(r.tempo_medio)
    if r.status == TIMEOUT:
        return "TIMEOUT"
    if r.status == IGNORADO:
        return "> limite"
    return r.status.upper()


def _ordenar_chaves(chaves) -> List[str]:
    ordem = {c: i for i, c in enumerate(algoritmos.ORDEM_ALGORITMOS)}
    return sorted(chaves, key=lambda c: ordem.get(c, 99))


def tabela_por_cenario(resultados: List[ResultadoTeste]) -> str:
    """Uma tabela por cenário: linhas = algoritmos, colunas = tamanhos (tempo médio)."""
    grupos: Dict[str, Dict] = defaultdict(dict)
    for r in resultados:
        grupos[r.cenario][(r.chave, r.tamanho)] = r

    partes = []
    for cenario in [c for c in config.CENARIOS if c in grupos] + \
                   [c for c in grupos if c not in config.CENARIOS]:
        mapa = grupos[cenario]
        tamanhos = sorted({n for _, n in mapa})
        chaves = _ordenar_chaves({k for k, _ in mapa})
        cab = ["Algoritmo", "Complexidade média"] + [f"n={config.fmt_int(n)}" for n in tamanhos]
        linhas = []
        for k in chaves:
            alg = algoritmos.obter(k)
            linhas.append([alg.nome, alg.medio] + [_celula(mapa.get((k, n))) for n in tamanhos])
        titulo = f"Cenário: {config.NOMES_CENARIOS.get(cenario, cenario)} (tempo médio de ordenação)"
        partes.append(titulo + "\n" + _tabela(cab, linhas, alinhar_esq=2))
    return "\n\n".join(partes)


def ranking(resultados: List[ResultadoTeste]) -> str:
    """Para cada cenário, classifica os algoritmos no MAIOR tamanho com tempo medido."""
    partes = []
    for cenario in config.CENARIOS:
        validos = [r for r in resultados if r.cenario == cenario and r.status == OK]
        if not validos:
            continue
        n_max = max(r.tamanho for r in validos)
        doc = sorted((r for r in validos if r.tamanho == n_max), key=lambda r: r.tempo_medio)
        melhor = doc[0].tempo_medio or 1e-12
        linhas = [[f"{i}º", r.algoritmo, config.fmt_tempo(r.tempo_medio),
                   f"{r.tempo_medio / melhor:,.1f}x".replace(",", "X").replace(".", ",").replace("X", ".")]
                  for i, r in enumerate(doc, 1)]
        partes.append(f"Ranking - {config.NOMES_CENARIOS[cenario]} (n={config.fmt_int(n_max)})\n"
                      + _tabela(["Pos.", "Algoritmo", "Tempo médio", "vs. 1º"], linhas, alinhar_esq=2))
    return "\n\n".join(partes)


def tabela_complexidades() -> str:
    """Tabela teórica de complexidade dos algoritmos implementados."""
    linhas = [[a.nome, a.melhor, a.medio, a.pior, a.memoria, "Sim" if a.estavel else "Não"]
              for a in algoritmos.ALGORITMOS.values()]
    return _tabela(["Algoritmo", "Melhor", "Médio", "Pior", "Memória extra", "Estável"],
                   linhas, alinhar_esq=1)


def relatorio_completo(resultados: List[ResultadoTeste], cabecalho: str = "") -> str:
    blocos = [b for b in (cabecalho, tabela_por_cenario(resultados), ranking(resultados)) if b]
    return "\n\n".join(blocos)


def salvar_relatorio(texto: str, caminho: Path = config.ARQ_TABELAS) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto + "\n", encoding="utf-8")
    return caminho
