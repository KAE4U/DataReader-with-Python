# APS – Estruturas de Dados (UNIP 2026/2)
## Sistema para Análise de Performance de Algoritmos de Ordenação de Dados

O contexto é o geoprocessamento das ~100 mil imagens de satélite da Floresta Amazônica que são catalogadas a cada 24 h. Cada número ordenado representa o código de uma imagem, no intervalo **0 a 99.999**.

---

## Como rodar

### 1. Clonar e instalar
```bash
git clone https://github.com/KAE4U/DataReader-with-Python.git
cd DataReader-with-Python
pip install -r requirements.txt
```
Use o **Python 3.12 ou 3.13**. A única biblioteca externa é o `matplotlib`.

> **Erro `SystemError: module numpy._core._multiarray_umath uses unknown slot ID`?**
> Isso acontece quando o NumPy instalado, que o matplotlib usa, não é compatível com a versão do Python. É comum com o Python 3.15, que é muito recente.
> Correção: instale o [Python 3.13](https://www.python.org/downloads/) e use-o explicitamente:
> ```bash
> py -3.13 -m pip install -r requirements.txt
> py -3.13 aps_simples.py
> ```
> Mesmo sem o matplotlib, o programa mede e mostra os tempos; só o gráfico deixa de ser gerado.

### 2. Versão simples (a que vamos usar na apresentação)
```bash
python aps_simples.py
```
- Ordena 1.000, 10.000, 50.000, 80.000 e 100.000 números aleatórios.
- Usa os **3 algoritmos mais rápidos** dos nossos testes: **Quick Sort, Merge Sort e Shell Sort**.
- Mostra o tempo de cada algoritmo para cada quantidade de dados.
- Gera `resultados_simples.csv` (abre no Excel) e `grafico_barras.png`.
- Roda em **poucos segundos**.

O cronômetro (`time.perf_counter()`) mede **só a ordenação**. O tempo de gerar os dados não entra.

### 3. Versão completa (opcional, para a monografia)
```bash
python main.py                      # menu interativo
python main.py --bateria interno    # todos os testes automaticamente
```
Além do que a versão simples faz, ela tem:
- 4 cenários: aleatório, já ordenado, invertido e semi-ordenado;
- leitura de arquivos `.txt` e `.csv` (`python main.py --gerar-arquivos` cria os arquivos de exemplo em `dados/`);
- entrada de valores digitados pelo usuário;
- listagem dos valores antes e depois da ordenação;
- repetições com média, mínimo e máximo;
- histórico em CSV e vários gráficos, salvos em `resultados/`.

---

## Resultado de exemplo (versão simples)

Medido em um Intel Xeon Platinum 8488C com Python 3.11. **Cada membro deve rodar na própria máquina**, porque o enunciado pede a comparação em diferentes máquinas.

| Algoritmo | 1.000 | 10.000 | 50.000 | 80.000 | 100.000 |
|---|---|---|---|---|---|
| Quick Sort | 0,0007 s | 0,0076 s | 0,0451 s | 0,0732 s | 0,0984 s |
| Merge Sort | 0,0012 s | 0,0147 s | 0,0852 s | 0,1490 s | 0,1899 s |
| Shell Sort | 0,0008 s | 0,0118 s | 0,0769 s | 0,1479 s | 0,2033 s |

![Gráfico de barras](grafico_barras.png)

## Por que esses 3 algoritmos?

Testamos 6 algoritmos (Bubble, Insertion, Shell, Heap, Merge e Quick) nos 4 cenários com 100.000 elementos e mantivemos os 3 com a menor soma de tempos:

| Algoritmo | Aleatório | Já ordenado | Invertido | Semi-ordenado | Soma |
|---|---|---|---|---|---|
| **Quick Sort** | 115,9 ms | 67,6 ms | 84,8 ms | 88,3 ms | **356,6 ms** |
| **Merge Sort** | 150,3 ms | 15,5 ms | 101,0 ms | 104,5 ms | **371,2 ms** |
| **Shell Sort** | 190,6 ms | 60,4 ms | 93,8 ms | 143,4 ms | **488,3 ms** |
| Heap Sort | 197,4 ms | 175,0 ms | 163,5 ms | 174,8 ms | 710,7 ms |
| Insertion Sort | > 60 s | 6,3 ms | > 60 s | 14,3 s | — |
| Bubble Sort | > 60 s | 3,7 ms | > 60 s | > 60 s | — |

Bubble e Insertion são O(n²): passaram de 60 segundos com dados aleatórios e invertidos. O Heap Sort é O(n log n), mas foi o mais lento dos quatro restantes em todos os cenários.

## Algoritmos

| Algoritmo | Melhor caso | Caso médio | Pior caso | Memória extra |
|---|---|---|---|---|
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) |
| Shell Sort | O(n log n) | ~O(n^1,3) | ~O(n^1,5) | O(1) |

## Estrutura do projeto
```
aps_simples.py     versão simples: um único arquivo
main.py            versão completa: ponto de entrada
aps/               módulos da versão completa (algoritmos, dados, benchmark, gráficos...)
testes/            testes de corretude:  python -m unittest discover -s testes
requirements.txt   dependências
```
