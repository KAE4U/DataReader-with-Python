"""
Aquisição de dados (NÃO entra na medição de tempo).

Fontes internas : geração aleatória em memória e digitação pelo usuário.
Fontes externas : leitura de arquivos .txt ou .csv previamente armazenados.
Cenários        : aleatório, já ordenado, invertido e semi-ordenado.
"""

from __future__ import annotations

import csv
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from . import config


class ErroDados(Exception):
    """Erro de aquisição/validação de dados (mensagem amigável ao usuário)."""


# ===========================================================================
# Fontes internas
# ===========================================================================
def gerar_aleatorios(n: int, semente: Optional[int] = None) -> List[int]:
    """Gera n inteiros uniformes em [VALOR_MIN, VALOR_MAX] (com repetição)."""
    if n <= 0:
        raise ErroDados("A quantidade de elementos deve ser maior que zero.")
    rng = random.Random(semente)
    return rng.choices(range(config.VALOR_MIN, config.VALOR_MAX + 1), k=n)


def interpretar_entrada_manual(texto: str) -> List[int]:
    """
    Converte uma string digitada pelo usuário em lista de inteiros.
    Aceita separadores: espaço, vírgula, ponto e vírgula ou quebra de linha.
    Valida o tipo e o intervalo 0..99.999.
    """
    tokens = [t for t in re.split(r"[\s,;]+", texto.strip()) if t]
    if not tokens:
        raise ErroDados("Nenhum valor informado.")
    valores, problemas = [], []
    for t in tokens:
        try:
            x = int(t)
        except ValueError:
            problemas.append(f"'{t}' não é inteiro")
            continue
        if not config.VALOR_MIN <= x <= config.VALOR_MAX:
            problemas.append(f"{x} fora do intervalo {config.VALOR_MIN}..{config.VALOR_MAX}")
            continue
        valores.append(x)
    if problemas:
        raise ErroDados("Valores inválidos: " + "; ".join(problemas[:10]))
    return valores


# ===========================================================================
# Cenários (disposição dos dados)
# ===========================================================================
def aplicar_cenario(base: List[int], cenario: str, semente: Optional[int] = None) -> List[int]:
    """
    Retorna uma NOVA lista com a disposição solicitada, a partir dos dados base.
    A lista base nunca é alterada.
    """
    if cenario == "aleatorio":
        return list(base)
    if cenario == "ordenado":
        return sorted(base)
    if cenario == "invertido":
        return sorted(base, reverse=True)
    if cenario == "semi_ordenado":
        return semi_ordenar(base, config.PERC_DESORDEM_SEMI, semente)
    raise ErroDados(f"Cenário desconhecido: {cenario}. Válidos: {', '.join(config.CENARIOS)}")


def semi_ordenar(base: List[int], perc: float, semente: Optional[int] = None) -> List[int]:
    """
    Ordena os dados e depois troca pares de posições aleatórias, de modo que
    aproximadamente 'perc' dos elementos fique fora do lugar.
    Ex.: perc=0.10 -> ~90% dos elementos já estão na posição final.
    """
    v = sorted(base)
    n = len(v)
    if n < 2:
        return v
    rng = random.Random(semente)
    trocas = max(1, int(n * perc / 2))  # cada troca desloca 2 elementos
    for _ in range(trocas):
        i, j = rng.randrange(n), rng.randrange(n)
        v[i], v[j] = v[j], v[i]
    return v


# ===========================================================================
# Fontes externas (arquivos)
# ===========================================================================
@dataclass
class LeituraArquivo:
    """Resultado da leitura de um arquivo, com estatísticas de validação."""
    caminho: Path
    valores: List[int] = field(default_factory=list)
    invalidos: int = 0          # tokens não numéricos (ex.: cabeçalho, texto)
    fora_intervalo: int = 0     # números fora de 0..99.999 (descartados)

    def resumo(self) -> str:
        return (f"{config.fmt_int(len(self.valores))} valores válidos lidos de '{self.caminho.name}'"
                f" | não numéricos: {self.invalidos} | fora do intervalo: {self.fora_intervalo}")


_COLUNAS_PREFERIDAS = ("codigo_imagem", "codigo", "valor", "id", "id_imagem")


def ler_arquivo(caminho: str | Path, coluna: Optional[str] = None) -> LeituraArquivo:
    """
    Lê valores inteiros de um arquivo .txt ou .csv.

    .txt -> qualquer separador (espaço, vírgula, ';', quebra de linha).
    .csv -> detecta o delimitador; usa a coluna informada, ou uma coluna
            conhecida (codigo_imagem, codigo, valor, id), ou a primeira.
    """
    caminho = Path(caminho).expanduser()
    if not caminho.is_file():
        raise ErroDados(f"Arquivo não encontrado: {caminho}")
    ext = caminho.suffix.lower()
    if ext not in (".txt", ".csv"):
        raise ErroDados(f"Extensão não suportada '{ext}'. Use .txt ou .csv.")

    leitura = LeituraArquivo(caminho)
    try:
        with caminho.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            if ext == ".txt":
                for linha in f:
                    for token in re.split(r"[\s,;]+", linha.strip()):
                        if token:
                            _registrar(leitura, token)
            else:
                _ler_csv(f, leitura, coluna)
    except OSError as e:
        raise ErroDados(f"Falha ao ler '{caminho}': {e}") from e

    if not leitura.valores:
        raise ErroDados(f"Nenhum valor válido encontrado em '{caminho.name}'.")
    return leitura


def _ler_csv(f, leitura: LeituraArquivo, coluna: Optional[str]) -> None:
    amostra = f.read(4096)
    f.seek(0)
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t|")
    except csv.Error:
        dialeto = csv.excel
    leitor = csv.reader(f, dialeto)

    primeira = next(leitor, None)
    if primeira is None:
        return
    cabecalho = [c.strip().lower() for c in primeira]
    tem_cabecalho = not all(_eh_inteiro(c) for c in cabecalho if c)

    idx = 0
    if tem_cabecalho:
        if coluna:
            if coluna.lower() not in cabecalho:
                raise ErroDados(f"Coluna '{coluna}' não existe. Colunas: {', '.join(cabecalho)}")
            idx = cabecalho.index(coluna.lower())
        else:
            idx = next((cabecalho.index(c) for c in _COLUNAS_PREFERIDAS if c in cabecalho), 0)
    elif primeira:
        _registrar(leitura, primeira[0])

    for linha in leitor:
        if idx < len(linha) and linha[idx].strip():
            _registrar(leitura, linha[idx].strip())


def _eh_inteiro(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def _registrar(leitura: LeituraArquivo, token: str) -> None:
    """Valida um token e o adiciona aos valores, atualizando as estatísticas."""
    try:
        x = int(token)
    except ValueError:
        leitura.invalidos += 1
        return
    if config.VALOR_MIN <= x <= config.VALOR_MAX:
        leitura.valores.append(x)
    else:
        leitura.fora_intervalo += 1


def salvar_txt(valores: List[int], caminho: str | Path) -> Path:
    """Salva um valor por linha."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(map(str, valores)) + "\n", encoding="utf-8")
    return caminho


def salvar_csv(valores: List[int], caminho: str | Path) -> Path:
    """Salva em CSV com cabeçalho (sequencia;codigo_imagem)."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["sequencia", "codigo_imagem"])
        w.writerows(enumerate(valores, start=1))
    return caminho


def caminho_arquivo_padrao(n: int, ext: str = ".txt") -> Path:
    return config.DIR_DADOS / f"{config.PREFIXO_ARQUIVO}{n}{ext}"


def gerar_arquivos_padrao(tamanhos=config.TAMANHOS_PADRAO,
                          semente: int = config.SEMENTE_PADRAO) -> List[Path]:
    """
    Gera os arquivos externos de entrada (um .txt e um .csv por tamanho)
    com semente fixa: todas as máquinas do grupo testam os MESMOS dados.
    """
    config.garantir_diretorios()
    gerados = []
    for n in tamanhos:
        valores = gerar_aleatorios(n, semente + n)
        gerados.append(salvar_txt(valores, caminho_arquivo_padrao(n, ".txt")))
        gerados.append(salvar_csv(valores, caminho_arquivo_padrao(n, ".csv")))
    return gerados


def carregar_arquivo_padrao(n: int) -> List[int]:
    """Carrega dados/satelite_<n>.txt (usado na bateria com dados externos)."""
    caminho = caminho_arquivo_padrao(n)
    if not caminho.exists():
        raise ErroDados(f"Arquivo '{caminho.name}' não existe. Gere-o pelo menu "
                        f"'Gerar arquivos de dados' ou com: python main.py --gerar-arquivos")
    leitura = ler_arquivo(caminho)
    if len(leitura.valores) < n:
        raise ErroDados(f"'{caminho.name}' tem {len(leitura.valores)} valores; esperado {n}.")
    return leitura.valores[:n]


def amostra_texto(v: List[int], k: int = 10) -> str:
    """Representação curta para listagem 'antes/depois' (primeiros e últimos k)."""
    if len(v) <= 2 * k:
        return str(v)
    ini = ", ".join(map(str, v[:k]))
    fim = ", ".join(map(str, v[-k:]))
    return f"[{ini}, ... ({config.fmt_int(len(v) - 2 * k)} omitidos) ..., {fim}]"
