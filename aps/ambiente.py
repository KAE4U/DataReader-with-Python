"""Identificação da máquina: permite comparar resultados entre computadores."""

from __future__ import annotations

import os
import platform
from functools import lru_cache
from typing import Dict


@lru_cache(maxsize=1)
def info_maquina() -> Dict[str, str]:
    return {
        "maquina": platform.node() or "desconhecida",
        "sistema": f"{platform.system()} {platform.release()}",
        "processador": _nome_processador(),
        "nucleos": str(os.cpu_count() or "?"),
        "python": f"{platform.python_implementation()} {platform.python_version()}",
    }


def _nome_processador() -> str:
    nome = platform.processor()
    # No Linux, platform.processor() costuma retornar só 'x86_64'
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for linha in f:
                    if linha.lower().startswith("model name"):
                        return linha.split(":", 1)[1].strip()
        except OSError:
            pass
    return nome or platform.machine() or "desconhecido"


def descricao() -> str:
    i = info_maquina()
    return (f"Máquina: {i['maquina']} | {i['sistema']} | CPU: {i['processador']} "
            f"({i['nucleos']} núcleos) | {i['python']}")
