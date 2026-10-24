"""
APS - Estruturas de Dados (UNIP) - 2026/2
Sistema para Análise de Performance de Algoritmos de Ordenação de Dados.

Contexto: geoprocessamento de ~100 mil imagens de satélite da Floresta Amazônica
catalogadas a cada 24 horas. Cada valor ordenado representa o código de
catalogação de uma imagem (intervalo 0 a 99.999).

Módulos:
    config      -> constantes e caminhos do projeto
    algoritmos  -> implementações dos algoritmos de ordenação + metadados
    dados       -> geração interna, cenários, leitura/escrita de arquivos
    benchmark   -> medição de tempo (somente a ordenação) com isolamento/timeout
    ambiente    -> identificação da máquina (comparação entre máquinas)
    historico   -> persistência do histórico de testes em CSV
    relatorios  -> tabelas comparativas no console/arquivo
    graficos    -> gráficos (matplotlib) Tamanho x Tempo
    interface   -> menu interativo (CLI)
"""

__version__ = "1.0.0"
