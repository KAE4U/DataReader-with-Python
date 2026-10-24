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
> Mesmo sem o matplotlib, o programa mede e mostra os tempos e gera o gráfico de barras em **SVG** com Python puro. O SVG abre no navegador e pode ser inserido no Word.

> **Importante:** rode **todos** os scripts com o mesmo Python (`py -3.13 main.py`, `py -3.13 aps_simples.py`). Se aparecer `No module named 'matplotlib'`, o aviso mostra qual Python está em uso e o comando para instalar nele. Evite usar `pip` sozinho: ele pode apontar para outro Python. Use `py -3.13 -m pip`.

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
| Quick Sort | 0,0007 s | 0,0075 s | 0,0446 s | 0,0729 s | 0,0953 s |
| Merge Sort | 0,0012 s | 0,0147 s | 0,0858 s | 0,1537 s | 0,1851 s |
| Shell Sort | 0,0008 s | 0,0124 s | 0,0769 s | 0,1435 s | 0,1930 s |

![Gráfico de barras](grafico_barras.png)

## Por que esses 3 algoritmos?

Testamos 6 algoritmos (Bubble, Insertion, Shell, Heap, Merge e Quick) com 100.000 números aleatórios e mantivemos os 3 mais rápidos:

| Algoritmo | Tempo (100.000 aleatórios) |
|---|---|
| **Quick Sort** | **115,9 ms** |
| **Merge Sort** | **150,3 ms** |
| **Shell Sort** | **190,6 ms** |
| Heap Sort | 197,4 ms |
| Insertion Sort | > 60 s |
| Bubble Sort | > 60 s |

Bubble e Insertion são O(n²) e passaram de 60 segundos. O Heap Sort é O(n log n), mas ficou atrás dos outros três.

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
