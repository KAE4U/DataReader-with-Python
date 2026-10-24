"""Interface de linha de comando (menu interativo) e rotinas de alto nível."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Sequence

from . import algoritmos, ambiente, benchmark, config, dados, graficos, historico, relatorios

LINHA = "=" * 78


# ===========================================================================
# Configuração da sessão
# ===========================================================================
@dataclass
class Configuracao:
    algoritmos: List[str] = field(default_factory=lambda: list(algoritmos.ORDEM_ALGORITMOS))
    cenarios: List[str] = field(default_factory=lambda: list(config.CENARIOS))
    tamanhos: List[int] = field(default_factory=lambda: list(config.TAMANHOS_PADRAO))
    repeticoes: int = config.REPETICOES_PADRAO
    timeout: Optional[float] = config.TIMEOUT_PADRAO
    gerar_graficos: bool = True

    def descricao(self) -> str:
        nomes = ", ".join(algoritmos.obter(a).nome for a in self.algoritmos)
        cens = ", ".join(config.NOMES_CENARIOS[c] for c in self.cenarios)
        tams = ", ".join(config.fmt_int(n) for n in self.tamanhos)
        lim = f"{self.timeout:.0f} s" if self.timeout else "sem limite"
        return (f"  Algoritmos : {nomes}\n  Cenários   : {cens}\n  Tamanhos   : {tams}\n"
                f"  Repetições : {self.repeticoes}   |   Tempo limite por execução: {lim}")


# ===========================================================================
# Entrada de dados com validação
# ===========================================================================
def ler_texto(msg: str, padrao: str = "") -> str:
    try:
        resp = input(msg).strip()
    except EOFError:
        raise KeyboardInterrupt from None
    return resp or padrao


def ler_inteiro(msg: str, minimo: int, maximo: int, padrao: Optional[int] = None) -> int:
    sufixo = f" [{padrao}]" if padrao is not None else ""
    while True:
        resp = ler_texto(f"{msg}{sufixo}: ")
        if not resp and padrao is not None:
            return padrao
        try:
            valor = int(resp.replace(".", ""))
        except ValueError:
            print(f"  [!] Digite um número inteiro entre {minimo} e {maximo}.")
            continue
        if minimo <= valor <= maximo:
            return valor
        print(f"  [!] Valor fora do intervalo ({minimo} a {maximo}).")


def ler_sim_nao(msg: str, padrao: bool = True) -> bool:
    op = "S/n" if padrao else "s/N"
    while True:
        resp = ler_texto(f"{msg} [{op}]: ").lower()
        if not resp:
            return padrao
        if resp in ("s", "sim", "y"):
            return True
        if resp in ("n", "nao", "não"):
            return False
        print("  [!] Responda 's' ou 'n'.")


def escolher_varios(titulo: str, opcoes: Sequence[str], rotulos: Sequence[str],
                    atuais: Sequence[str]) -> List[str]:
    """Seleção múltipla: '1,3,4', 'todos' ou Enter para manter a seleção atual."""
    print(f"\n{titulo}")
    for i, (op, rot) in enumerate(zip(opcoes, rotulos), 1):
        marca = "x" if op in atuais else " "
        print(f"  [{marca}] {i} - {rot}")
    while True:
        resp = ler_texto("Números separados por vírgula, 'todos' ou Enter para manter: ").lower()
        if not resp:
            return list(atuais)
        if resp in ("todos", "t", "*"):
            return list(opcoes)
        try:
            idx = sorted({int(x) for x in resp.replace(" ", "").split(",") if x})
            if idx and all(1 <= i <= len(opcoes) for i in idx):
                return [opcoes[i - 1] for i in idx]
        except ValueError:
            pass
        print("  [!] Seleção inválida.")


def escolher_um(titulo: str, opcoes: Sequence[str], rotulos: Sequence[str]) -> str:
    print(f"\n{titulo}")
    for i, rot in enumerate(rotulos, 1):
        print(f"  {i} - {rot}")
    return opcoes[ler_inteiro("Opção", 1, len(opcoes), 1) - 1]


# ===========================================================================
# Rotinas de alto nível (também usadas pela linha de comando não interativa)
# ===========================================================================
def obter_base_interna(n: int) -> List[int]:
    """Fonte interna: números aleatórios gerados em memória com semente fixa."""
    return dados.gerar_aleatorios(n, config.SEMENTE_PADRAO + n)


def rodar_bateria(cfg: Configuracao, fonte: str) -> List[benchmark.ResultadoTeste]:
    """Executa a bateria completa e consolida a saída (tabelas, CSV, gráficos)."""
    obter_base: Callable[[int], List[int]] = (
        obter_base_interna if fonte == "interno" else dados.carregar_arquivo_padrao)

    print(f"\n{LINHA}\nBATERIA DE TESTES - fonte de dados: {fonte.upper()}\n{LINHA}")
    print(ambiente.descricao())
    print(cfg.descricao())
    print("(Ctrl+C interrompe e mantém os resultados parciais)")

    try:
        resultados, interrompido = benchmark.executar_bateria(
            cfg.algoritmos, cfg.cenarios, cfg.tamanhos, obter_base, fonte,
            cfg.repeticoes, cfg.timeout)
    except dados.ErroDados as e:
        print(f"\n[ERRO] {e}")
        return []

    finalizar(resultados, fonte, cfg.gerar_graficos, interrompido)
    return resultados


def finalizar(resultados: List[benchmark.ResultadoTeste], fonte: str,
              gerar_graficos: bool = True, interrompido: bool = False) -> None:
    """Exibe tabelas, salva histórico CSV, relatório .txt e gráficos."""
    if not resultados:
        print("Nenhum resultado para consolidar.")
        return
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    cab = (f"RESULTADOS - fonte: {fonte}{' (PARCIAL)' if interrompido else ''} - "
           f"{datetime.now():%d/%m/%Y %H:%M}\n{ambiente.descricao()}")
    texto = relatorios.relatorio_completo(resultados, cab)
    print(f"\n{LINHA}\n{texto}\n{LINHA}")
    print("Legenda: TIMEOUT = excedeu o tempo limite | '> limite' = não executado porque "
          "um tamanho menor já excedeu o limite.")

    try:
        arq = historico.salvar(resultados)
        print(f"\n[OK] Histórico atualizado: {arq}")
    except OSError as e:
        print(f"\n[ERRO] {e}")

    arq_tab = relatorios.salvar_relatorio(
        texto, config.DIR_RESULTADOS / f"tabelas_{fonte}_{carimbo}.txt")
    print(f"[OK] Tabelas salvas em: {arq_tab}")

    if gerar_graficos:
        _gerar_graficos(resultados, config.DIR_GRAFICOS / f"{fonte}_{carimbo}",
                        f"Fonte: {fonte} | {ambiente.info_maquina()['processador']}")


def _gerar_graficos(resultados, pasta: Path, subtitulo: str) -> None:
    try:
        arquivos = graficos.gerar_todos(resultados, pasta, subtitulo)
    except RuntimeError as e:
        print(f"[AVISO] {e}")
        return
    if arquivos:
        print(f"[OK] {len(arquivos)} gráficos gerados em: {pasta}")
    else:
        print("[AVISO] Não há tempos válidos para gerar gráficos.")


# ===========================================================================
# Opções do menu
# ===========================================================================
def _menu_teste_individual(cfg: Configuracao) -> None:
    fonte = escolher_um("Fonte dos dados:", ["gerado", "manual", "arquivo"], [
        "Interna - gerar números aleatórios (0 a 99.999)",
        "Interna - digitar os valores",
        "Externa - ler arquivo .txt ou .csv",
    ])
    try:
        if fonte == "gerado":
            n = ler_inteiro("Quantidade de elementos", 1, 1_000_000, 1_000)
            base = dados.gerar_aleatorios(n)
        elif fonte == "manual":
            texto = ler_texto("Digite os valores (separados por espaço ou vírgula):\n> ")
            base = dados.interpretar_entrada_manual(texto)
        else:
            caminho = ler_texto(f"Caminho do arquivo [{dados.caminho_arquivo_padrao(1000)}]: ",
                                str(dados.caminho_arquivo_padrao(1000)))
            leitura = dados.ler_arquivo(caminho)
            print(f"  {leitura.resumo()}")
            base = leitura.valores
    except dados.ErroDados as e:
        print(f"\n[ERRO] {e}")
        return

    cenario = escolher_um("Disposição dos dados:", list(config.CENARIOS),
                          [config.NOMES_CENARIOS[c] for c in config.CENARIOS])
    entrada = dados.aplicar_cenario(base, cenario)
    chaves = escolher_varios("Algoritmos:", algoritmos.ORDEM_ALGORITMOS,
                             [a.nome for a in algoritmos.ALGORITMOS.values()], cfg.algoritmos)

    print(f"\nANTES  ({config.fmt_int(len(entrada))} elementos): {dados.amostra_texto(entrada)}")
    resultados, ultima = [], None
    for ch in chaves:
        r, ordenada = benchmark.teste_individual(ch, entrada, fonte, cenario,
                                                 cfg.repeticoes, cfg.timeout)
        resultados.append(r)
        if r.status == benchmark.OK:
            ultima = ordenada
            print(f"  {r.algoritmo:<22} média {config.fmt_tempo(r.tempo_medio):>13} | "
                  f"mín {config.fmt_tempo(r.tempo_min)} | máx {config.fmt_tempo(r.tempo_max)}")
        else:
            print(f"  {r.algoritmo:<22} {r.status.upper()} {r.observacao}")
    if ultima is not None:
        print(f"DEPOIS: {dados.amostra_texto(ultima)}")
        if ler_sim_nao("Exibir a lista ordenada completa?", False):
            print(ultima)
        if ler_sim_nao("Salvar entrada e saída em arquivo?", False):
            carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
            a = dados.salvar_txt(entrada, config.DIR_RESULTADOS / f"entrada_{carimbo}.txt")
            b = dados.salvar_txt(ultima, config.DIR_RESULTADOS / f"ordenado_{carimbo}.txt")
            print(f"  [OK] {a}\n  [OK] {b}")
    if resultados and ler_sim_nao("Registrar no histórico CSV?", True):
        print(f"  [OK] {historico.salvar(resultados)}")


def _menu_gerar_arquivos() -> None:
    print(f"\nSerão gerados .txt e .csv em '{config.DIR_DADOS}' para os tamanhos "
          f"{', '.join(config.fmt_int(n) for n in config.TAMANHOS_PADRAO)} (semente {config.SEMENTE_PADRAO}).")
    if ler_sim_nao("Confirmar?", True):
        for p in dados.gerar_arquivos_padrao():
            print(f"  [OK] {p}")


def _menu_historico() -> List[benchmark.ResultadoTeste]:
    todos = historico.carregar()
    if not todos:
        print(f"\nHistórico vazio ({config.ARQ_HISTORICO}).")
        return []
    maquinas = sorted({r.maquina for r in todos})
    fontes = sorted({r.fonte for r in todos})
    print(f"\n{len(todos)} registros | máquinas: {', '.join(maquinas)} | fontes: {', '.join(fontes)}")
    maq = maquinas[0] if len(maquinas) == 1 else escolher_um("Máquina:", maquinas, maquinas)
    fon = fontes[0] if len(fontes) == 1 else escolher_um("Fonte:", fontes, fontes)
    filtrados = historico.ultima_execucao_por_combinacao(todos, maq, fon)
    print(relatorios.relatorio_completo(filtrados, f"HISTÓRICO - {maq} - fonte: {fon} "
                                                   f"(teste mais recente de cada combinação)"))
    return filtrados


def _menu_graficos_historico() -> None:
    filtrados = _menu_historico()
    if filtrados:
        pasta = config.DIR_GRAFICOS / f"historico_{datetime.now():%Y%m%d_%H%M%S}"
        _gerar_graficos(filtrados, pasta, f"Histórico - {filtrados[0].maquina}")


def _menu_configuracoes(cfg: Configuracao) -> None:
    cfg.algoritmos = escolher_varios("Algoritmos:", algoritmos.ORDEM_ALGORITMOS,
                                     [f"{a.nome} - {a.medio}" for a in algoritmos.ALGORITMOS.values()],
                                     cfg.algoritmos)
    cfg.cenarios = escolher_varios("Cenários:", list(config.CENARIOS),
                                   [config.NOMES_CENARIOS[c] for c in config.CENARIOS], cfg.cenarios)
    tams = [str(n) for n in config.TAMANHOS_PADRAO]
    cfg.tamanhos = [int(t) for t in escolher_varios(
        "Tamanhos:", tams, [config.fmt_int(n) for n in config.TAMANHOS_PADRAO],
        [str(n) for n in cfg.tamanhos])]
    cfg.repeticoes = ler_inteiro("Repetições por medição", 1, 50, cfg.repeticoes)
    t = ler_inteiro("Tempo limite por execução em segundos (0 = sem limite)", 0, 86_400,
                    int(cfg.timeout or 0))
    cfg.timeout = float(t) if t > 0 else None
    cfg.gerar_graficos = ler_sim_nao("Gerar gráficos ao fim das baterias?", cfg.gerar_graficos)
    print("\nConfiguração atual:\n" + cfg.descricao())


def menu(cfg: Optional[Configuracao] = None) -> None:
    cfg = cfg or Configuracao()
    config.garantir_diretorios()
    print(f"{LINHA}\n  APS - ESTRUTURAS DE DADOS - UNIP\n"
          f"  Análise de Performance de Algoritmos de Ordenação\n"
          f"  Contexto: catálogo diário de ~100 mil imagens de satélite da Amazônia\n{LINHA}")
    print(ambiente.descricao())

    opcoes = {
        "1": ("Bateria completa - dados INTERNOS (gerados em memória)", lambda: rodar_bateria(cfg, "interno")),
        "2": ("Bateria completa - dados EXTERNOS (arquivos em dados/)", lambda: rodar_bateria(cfg, "externo")),
        "3": ("Teste individual (gerar / digitar / arquivo) com listagem antes e depois",
              lambda: _menu_teste_individual(cfg)),
        "4": ("Gerar arquivos de dados externos (.txt/.csv)", _menu_gerar_arquivos),
        "5": ("Exibir histórico de testes (CSV)", _menu_historico),
        "6": ("Gerar gráficos a partir do histórico", _menu_graficos_historico),
        "7": ("Configurações (algoritmos, cenários, tamanhos, repetições, limite)",
              lambda: _menu_configuracoes(cfg)),
        "8": ("Tabela teórica de complexidade", lambda: print(relatorios.tabela_complexidades())),
        "0": ("Sair", None),
    }
    while True:
        print(f"\n{LINHA}\nMENU PRINCIPAL")
        for k, (rot, _) in opcoes.items():
            print(f"  {k} - {rot}")
        op = ""
        try:
            op = ler_texto("Opção: ")
            if op == "0":
                print("Encerrando.")
                return
            if op not in opcoes:
                print("  [!] Opção inválida.")
                continue
            opcoes[op][1]()
        except KeyboardInterrupt:
            print("\n[!] Operação cancelada.")
            if op == "0" or not ler_sim_nao_seguro("Voltar ao menu?"):
                return
        except Exception as e:  # noqa: BLE001 - mantém o programa vivo diante de erros inesperados
            print(f"\n[ERRO inesperado] {type(e).__name__}: {e}")


def ler_sim_nao_seguro(msg: str) -> bool:
    try:
        return ler_sim_nao(msg, True)
    except KeyboardInterrupt:
        return False
