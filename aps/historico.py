"""
Persistência do histórico de testes em CSV.

Formato compatível com Excel em português: separador ';', decimal ',',
codificação UTF-8 com BOM. Os testes são ACRESCENTADOS ao arquivo, formando
um histórico de execuções (inclusive de máquinas diferentes, se o arquivo
for compartilhado entre os integrantes do grupo).
"""

from __future__ import annotations

import csv
from dataclasses import fields
from pathlib import Path
from typing import List, Optional

from . import config
from .benchmark import ResultadoTeste

CAMPOS = [f.name for f in fields(ResultadoTeste)]
_NUMERICOS = {"tempo_medio", "tempo_min", "tempo_max", "desvio_padrao"}
_INTEIROS = {"tamanho", "repeticoes"}


def _fmt(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float):
        return f"{valor:.9f}".replace(".", ",")
    return str(valor)


def salvar(resultados: List[ResultadoTeste], caminho: Path = config.ARQ_HISTORICO) -> Path:
    """Acrescenta os resultados ao histórico (cria o arquivo com cabeçalho se preciso)."""
    if not resultados:
        return caminho
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    novo = not caminho.exists() or caminho.stat().st_size == 0
    try:
        with caminho.open("a", encoding="utf-8-sig" if novo else "utf-8", newline="") as f:
            w = csv.writer(f, delimiter=";")
            if novo:
                w.writerow(CAMPOS)
            for r in resultados:
                d = r.como_dict()
                w.writerow([_fmt(d[c]) for c in CAMPOS])
    except PermissionError as e:
        raise OSError(f"Não foi possível gravar '{caminho}'. O arquivo está aberto em "
                      f"outro programa (ex.: Excel)? Detalhe: {e}") from e
    return caminho


def carregar(caminho: Path = config.ARQ_HISTORICO) -> List[ResultadoTeste]:
    """Lê o histórico completo. Linhas corrompidas são ignoradas."""
    caminho = Path(caminho)
    if not caminho.exists():
        return []
    resultados = []
    with caminho.open("r", encoding="utf-8-sig", newline="") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            try:
                resultados.append(ResultadoTeste(**{c: _converter(c, linha.get(c, "")) for c in CAMPOS}))
            except (TypeError, ValueError):
                continue
    return resultados


def _converter(campo: str, valor: Optional[str]):
    valor = (valor or "").strip()
    if campo in _INTEIROS:
        return int(valor)
    if campo in _NUMERICOS:
        return float(valor.replace(",", ".")) if valor else None
    return valor


def ultima_execucao_por_combinacao(resultados: List[ResultadoTeste],
                                   maquina: Optional[str] = None,
                                   fonte: Optional[str] = None) -> List[ResultadoTeste]:
    """
    Mantém apenas o teste mais recente de cada (máquina, fonte, algoritmo, cenário, tamanho).
    Útil para gerar gráficos a partir de um histórico com várias execuções.
    """
    ultimos = {}
    for r in resultados:
        if maquina and r.maquina != maquina:
            continue
        if fonte and r.fonte != fonte:
            continue
        ultimos[(r.maquina, r.fonte, r.chave, r.cenario, r.tamanho)] = r
    return list(ultimos.values())
