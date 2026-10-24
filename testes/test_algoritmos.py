"""
Testes de corretude dos algoritmos (não medem tempo).
Execute com:  python -m unittest discover -s testes -v
"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aps import algoritmos, config, dados  # noqa: E402


class TestAlgoritmos(unittest.TestCase):
    CASOS_FIXOS = [[], [1], [2, 1], [1, 2], [3, 3, 3], [5, 1, 4, 2, 3], [0, 99_999, 0, 99_999]]

    def _verificar(self, entrada):
        for chave, alg in algoritmos.ALGORITMOS.items():
            with self.subTest(algoritmo=chave, n=len(entrada)):
                v = list(entrada)
                alg.funcao(v)
                self.assertEqual(v, sorted(entrada))

    def test_casos_fixos(self):
        for caso in self.CASOS_FIXOS:
            self._verificar(caso)

    def test_dados_aleatorios(self):
        self._verificar(dados.gerar_aleatorios(2_000, 42))

    def test_muitos_repetidos(self):
        rng = random.Random(1)
        self._verificar([rng.randint(0, 5) for _ in range(3_000)])

    def test_quick_sort_grande_ordenado_sem_recursion_error(self):
        v = list(range(100_000))
        algoritmos.quick_sort(v)
        self.assertEqual(v, list(range(100_000)))


class TestDados(unittest.TestCase):
    def test_intervalo(self):
        v = dados.gerar_aleatorios(10_000, 1)
        self.assertTrue(all(config.VALOR_MIN <= x <= config.VALOR_MAX for x in v))

    def test_entrada_manual(self):
        self.assertEqual(dados.interpretar_entrada_manual("5, 3;1 99999"), [5, 3, 1, 99_999])
        with self.assertRaises(dados.ErroDados):
            dados.interpretar_entrada_manual("1 abc 100000")

    def test_cenario_aleatorio_nao_altera_base(self):
        base = dados.gerar_aleatorios(1_000, 3)
        copia = dados.aplicar_cenario(base)
        self.assertEqual(copia, base)
        self.assertIsNot(copia, base)


if __name__ == "__main__":
    unittest.main()
