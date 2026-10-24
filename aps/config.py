"""Constantes globais e caminhos do projeto."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos (relativos à raiz do projeto, garantindo portabilidade)
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_DADOS = RAIZ / "dados"
DIR_RESULTADOS = RAIZ / "resultados"
DIR_GRAFICOS = DIR_RESULTADOS / "graficos"
ARQ_HISTORICO = DIR_RESULTADOS / "historico_testes.csv"
ARQ_TABELAS = DIR_RESULTADOS / "tabelas_comparativas.txt"

# ---------------------------------------------------------------------------
# Domínio dos dados (enunciado da APS)
# ---------------------------------------------------------------------------
VALOR_MIN = 0
VALOR_MAX = 99_999

# Tamanhos de amostra exigidos pelo enunciado
TAMANHOS_PADRAO = (1_000, 10_000, 50_000, 80_000, 100_000)

# Disposição dos dados: apenas aleatórios (dados desordenados, como no enunciado)
CENARIOS = ("aleatorio",)
NOMES_CENARIOS = {"aleatorio": "Aleatório"}

# Semente padrão: garante que máquinas diferentes ordenem EXATAMENTE os mesmos dados
SEMENTE_PADRAO = 2026

# Parâmetros padrão do benchmark
REPETICOES_PADRAO = 3          # cada medição é repetida e são reportados média/mín/máx
TIMEOUT_PADRAO = 120.0         # segundos por execução (evita esperas de horas com O(n²))

# Prefixo dos arquivos externos gerados para a bateria de testes
PREFIXO_ARQUIVO = "satelite_"


def garantir_diretorios() -> None:
    """Cria as pastas de dados e resultados, caso ainda não existam."""
    for pasta in (DIR_DADOS, DIR_RESULTADOS, DIR_GRAFICOS):
        pasta.mkdir(parents=True, exist_ok=True)


def fmt_int(n: int) -> str:
    """Formata inteiro no padrão brasileiro (100000 -> '100.000')."""
    return f"{n:,}".replace(",", ".")


def fmt_tempo(segundos: float) -> str:
    """Formata um tempo em segundos de forma legível (ms abaixo de 1 s)."""
    if segundos < 1:
        return f"{segundos * 1000:.3f} ms".replace(".", ",")
    return f"{segundos:.4f} s".replace(".", ",")
