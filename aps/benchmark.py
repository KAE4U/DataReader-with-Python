"""
Núcleo de medição de desempenho.

Regras de medição (enunciado da APS):
    * A unidade de comparação é o TEMPO TOTAL DE ORDENAÇÃO.
    * O tempo de aquisição (geração, leitura de arquivo, aplicação do cenário,
      cópia da lista e validação do resultado) NÃO é contabilizado.

Como isso é garantido:
    1. Os dados são preparados ANTES do cronômetro.
    2. Uma cópia nova é feita antes de cada repetição (fora do cronômetro),
       para que nenhuma repetição receba dados já ordenados pela anterior.
    3. O coletor de lixo (gc) é desligado durante a ordenação para não
       introduzir pausas aleatórias na medição.
    4. time.perf_counter() (relógio monotônico de maior resolução) envolve
       APENAS a chamada do algoritmo.
    5. A corretude é verificada DEPOIS de parar o cronômetro.

Isolamento e tempo limite:
    Algoritmos O(n²) em Python puro podem levar dezenas de minutos com
    100.000 elementos. Cada ordenação roda em um processo filho; se exceder
    o tempo limite, o processo é encerrado e o teste é marcado como TIMEOUT.
    Tamanhos maiores do mesmo algoritmo/cenário são então ignorados, pois
    certamente também excederiam o limite.
"""

from __future__ import annotations

import gc
import multiprocessing as mp
import signal
import statistics
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Callable, Iterable, List, Optional, Tuple

from . import algoritmos, ambiente, config, dados

# Status possíveis de um teste
OK, TIMEOUT, IGNORADO, ERRO, INVALIDO = "ok", "timeout", "ignorado", "erro", "invalido"


# ===========================================================================
# Medição pura (executada no processo filho ou no próprio processo)
# ===========================================================================
def medir_ordenacao(chave: str, entrada: List[int], devolver: bool = False
                    ) -> Tuple[float, bool, Optional[List[int]]]:
    """
    Ordena uma CÓPIA de 'entrada' e retorna (tempo_em_segundos, ordenou_corretamente,
    lista_ordenada|None). Somente a chamada do algoritmo é cronometrada.
    """
    funcao = algoritmos.obter(chave).funcao
    copia = list(entrada)                      # fora do cronômetro

    gc_ativo = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        inicio = time.perf_counter()           # >>> início da medição
        funcao(copia)
        fim = time.perf_counter()              # <<< fim da medição
    finally:
        if gc_ativo:
            gc.enable()

    correto = copia == sorted(entrada)         # validação fora do cronômetro
    return fim - inicio, correto, (copia if devolver else None)


def _laco_trabalhador(conexao) -> None:
    """Processo filho: recebe (chave, dados, devolver) e responde com a medição."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)   # Ctrl+C é tratado pelo processo pai
    while True:
        try:
            msg = conexao.recv()
        except (EOFError, OSError):
            break
        if msg is None:
            break
        chave, entrada, devolver = msg
        try:
            conexao.send(("ok",) + medir_ordenacao(chave, entrada, devolver))
        except Exception as e:  # noqa: BLE001 - erro é repassado ao processo pai
            conexao.send(("erro", f"{type(e).__name__}: {e}"))


@dataclass
class Execucao:
    status: str
    tempo: float = 0.0
    resultado: Optional[List[int]] = None
    mensagem: str = ""


class Executor:
    """
    Executa ordenações em um processo trabalhador reutilizável, com tempo limite.
    Se timeout for None, executa no próprio processo (sem limite).
    """

    def __init__(self, timeout: Optional[float] = config.TIMEOUT_PADRAO):
        self.timeout = timeout if timeout and timeout > 0 else None
        self._proc: Optional[mp.Process] = None
        self._conn = None

    # -- ciclo de vida -------------------------------------------------------
    def _iniciar(self) -> None:
        pai, filho = mp.Pipe()
        self._proc = mp.Process(target=_laco_trabalhador, args=(filho,), daemon=True)
        self._proc.start()
        filho.close()
        self._conn = pai

    def _matar(self) -> None:
        if self._proc is not None:
            self._proc.terminate()
            self._proc.join(timeout=5)
            if self._proc.is_alive():
                self._proc.kill()
                self._proc.join()
        if self._conn is not None:
            self._conn.close()
        self._proc = self._conn = None

    def fechar(self) -> None:
        if self._proc is not None and self._proc.is_alive():
            try:
                self._conn.send(None)
                self._proc.join(timeout=2)
            except (OSError, BrokenPipeError):
                pass
        self._matar()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.fechar()

    # -- execução --------------------------------------------------------------
    def executar(self, chave: str, entrada: List[int], devolver: bool = False) -> Execucao:
        if self.timeout is None:
            try:
                t, ok, res = medir_ordenacao(chave, entrada, devolver)
            except Exception as e:  # noqa: BLE001
                return Execucao(ERRO, mensagem=f"{type(e).__name__}: {e}")
            return Execucao(OK if ok else INVALIDO, t, res)

        if self._proc is None or not self._proc.is_alive():
            self._iniciar()
        try:
            self._conn.send((chave, entrada, devolver))
            # margem extra para a transferência dos dados entre processos
            if not self._conn.poll(self.timeout + 5):
                self._matar()
                return Execucao(TIMEOUT, self.timeout,
                                mensagem=f"excedeu {self.timeout:.0f} s")
            resposta = self._conn.recv()
        except (EOFError, OSError, BrokenPipeError) as e:
            self._matar()
            return Execucao(ERRO, mensagem=f"processo trabalhador falhou: {e}")

        if resposta[0] == "erro":
            return Execucao(ERRO, mensagem=resposta[1])
        _, t, ok, res = resposta
        if t > self.timeout:
            return Execucao(TIMEOUT, t, mensagem=f"excedeu {self.timeout:.0f} s")
        return Execucao(OK if ok else INVALIDO, t, res)


# ===========================================================================
# Resultado consolidado de um teste (uma linha do histórico CSV)
# ===========================================================================
@dataclass
class ResultadoTeste:
    data_hora: str
    maquina: str
    sistema: str
    processador: str
    python: str
    fonte: str
    algoritmo: str
    chave: str
    complexidade_media: str
    cenario: str
    tamanho: int
    repeticoes: int
    tempo_medio: Optional[float]
    tempo_min: Optional[float]
    tempo_max: Optional[float]
    desvio_padrao: Optional[float]
    status: str
    observacao: str = ""

    def como_dict(self) -> dict:
        return asdict(self)


def _novo_resultado(chave, cenario, n, fonte, tempos, status, obs="") -> ResultadoTeste:
    alg = algoritmos.obter(chave)
    info = ambiente.info_maquina()
    tem = bool(tempos) and status == OK
    return ResultadoTeste(
        data_hora=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        maquina=info["maquina"], sistema=info["sistema"],
        processador=info["processador"], python=info["python"],
        fonte=fonte, algoritmo=alg.nome, chave=chave,
        complexidade_media=alg.medio, cenario=cenario, tamanho=n,
        repeticoes=len(tempos),
        tempo_medio=statistics.fmean(tempos) if tem else None,
        tempo_min=min(tempos) if tem else None,
        tempo_max=max(tempos) if tem else None,
        desvio_padrao=(statistics.stdev(tempos) if len(tempos) > 1 else 0.0) if tem else None,
        status=status, observacao=obs,
    )


# ===========================================================================
# Bateria de testes
# ===========================================================================
def executar_bateria(
    chaves: Iterable[str],
    cenarios: Iterable[str],
    tamanhos: Iterable[int],
    obter_base: Callable[[int], List[int]],
    fonte: str,
    repeticoes: int = config.REPETICOES_PADRAO,
    timeout: Optional[float] = config.TIMEOUT_PADRAO,
    progresso: Optional[Callable[[str], None]] = print,
) -> Tuple[List[ResultadoTeste], bool]:
    """
    Executa todas as combinações algoritmo × cenário × tamanho.

    obter_base(n) -> lista base com n elementos (gerada ou lida de arquivo).
    Retorna (resultados, interrompido_pelo_usuario).
    """
    chaves, cenarios = list(chaves), list(cenarios)
    tamanhos = sorted(set(tamanhos))
    total = len(chaves) * len(cenarios) * len(tamanhos)
    resultados: List[ResultadoTeste] = []
    estourados = set()          # (chave, cenario) que já deram timeout
    contador = 0
    log = progresso or (lambda _m: None)

    # Aquisição de dados: feita uma única vez por tamanho, fora do cronômetro
    bases = {}
    for n in tamanhos:
        bases[n] = obter_base(n)

    with Executor(timeout) as executor:
        try:
            for cenario in cenarios:
                log(f"\n=== Cenário: {config.NOMES_CENARIOS[cenario]} ===")
                for n in tamanhos:
                    entrada = dados.aplicar_cenario(bases[n], cenario, config.SEMENTE_PADRAO + n)
                    for chave in chaves:
                        contador += 1
                        prefixo = (f"[{contador:>3}/{total}] {algoritmos.obter(chave).nome:<22} "
                                   f"n={config.fmt_int(n):>7}")
                        if (chave, cenario) in estourados:
                            r = _novo_resultado(chave, cenario, n, fonte, [], IGNORADO,
                                                "tamanho menor já excedeu o tempo limite")
                            resultados.append(r)
                            log(f"{prefixo} -> ignorado (tamanho menor excedeu o limite)")
                            continue

                        tempos, status, obs = [], OK, ""
                        for _ in range(max(1, repeticoes)):
                            ex = executor.executar(chave, entrada)
                            if ex.status != OK:
                                status, obs = ex.status, ex.mensagem
                                break
                            tempos.append(ex.tempo)

                        if status == TIMEOUT:
                            estourados.add((chave, cenario))
                        r = _novo_resultado(chave, cenario, n, fonte, tempos, status, obs)
                        resultados.append(r)
                        if status == OK:
                            log(f"{prefixo} -> média {config.fmt_tempo(r.tempo_medio):>13}"
                                f" (mín {config.fmt_tempo(r.tempo_min)})")
                        else:
                            log(f"{prefixo} -> {status.upper()} {obs}")
        except KeyboardInterrupt:
            log("\n[!] Bateria interrompida pelo usuário. Resultados parciais mantidos.")
            return resultados, True
    return resultados, False


def teste_individual(chave: str, entrada: List[int], fonte: str, cenario: str,
                     repeticoes: int, timeout: Optional[float]
                     ) -> Tuple[ResultadoTeste, Optional[List[int]]]:
    """Executa um único algoritmo e devolve o resultado e a lista ordenada."""
    tempos, status, obs, ordenada = [], OK, "", None
    with Executor(timeout) as executor:
        for i in range(max(1, repeticoes)):
            ex = executor.executar(chave, entrada, devolver=(i == 0))
            if ex.status != OK:
                status, obs = ex.status, ex.mensagem
                break
            if i == 0:
                ordenada = ex.resultado
            tempos.append(ex.tempo)
    return _novo_resultado(chave, cenario, len(entrada), fonte, tempos, status, obs), ordenada
