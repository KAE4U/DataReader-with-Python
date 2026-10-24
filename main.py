#!/usr/bin/env python3
"""
APS - Estruturas de Dados - UNIP 2026/2
Sistema para Análise de Performance de Algoritmos de Ordenação de Dados.

Uso:
    python main.py                       # menu interativo
    python main.py --bateria interno     # bateria completa com dados gerados em memória
    python main.py --bateria externo     # bateria completa com arquivos de dados/
    python main.py --gerar-arquivos      # cria dados/satelite_<n>.txt/.csv
    python main.py --bateria interno --tamanhos 1000 10000 --algoritmos quick merge
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import sys

from aps import algoritmos, config, dados, interface


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Análise de performance de algoritmos de ordenação (APS UNIP).")
    p.add_argument("--bateria", choices=["interno", "externo"],
                   help="executa a bateria completa sem menu interativo")
    p.add_argument("--gerar-arquivos", action="store_true",
                   help="gera os arquivos externos de entrada em dados/")
    p.add_argument("--algoritmos", nargs="+", choices=algoritmos.ORDEM_ALGORITMOS,
                   default=algoritmos.ORDEM_ALGORITMOS)
    p.add_argument("--cenarios", nargs="+", choices=config.CENARIOS, default=list(config.CENARIOS))
    p.add_argument("--tamanhos", nargs="+", type=int, default=list(config.TAMANHOS_PADRAO))
    p.add_argument("--repeticoes", type=int, default=config.REPETICOES_PADRAO)
    p.add_argument("--timeout", type=float, default=config.TIMEOUT_PADRAO,
                   help="tempo limite (s) por execução; 0 = sem limite")
    p.add_argument("--sem-graficos", action="store_true")
    return p


def main(argv=None) -> int:
    args = criar_parser().parse_args(argv)
    config.garantir_diretorios()

    invalidos = [n for n in args.tamanhos if n <= 0]
    if invalidos or args.repeticoes < 1:
        print("[ERRO] Tamanhos e repetições devem ser inteiros positivos.")
        return 2

    if args.gerar_arquivos:
        for caminho in dados.gerar_arquivos_padrao(sorted(set(args.tamanhos) | set(config.TAMANHOS_PADRAO))):
            print(f"[OK] {caminho}")

    cfg = interface.Configuracao(
        algoritmos=args.algoritmos, cenarios=args.cenarios, tamanhos=sorted(set(args.tamanhos)),
        repeticoes=args.repeticoes, timeout=args.timeout if args.timeout > 0 else None,
        gerar_graficos=not args.sem_graficos)

    if args.bateria:
        return 0 if interface.rodar_bateria(cfg, args.bateria) else 1
    if not args.gerar_arquivos:
        try:
            interface.menu(cfg)
        except KeyboardInterrupt:
            print("\nEncerrado pelo usuário.")
    return 0


if __name__ == "__main__":
    mp.freeze_support()      # necessário no Windows (multiprocessing com 'spawn')
    sys.exit(main())
