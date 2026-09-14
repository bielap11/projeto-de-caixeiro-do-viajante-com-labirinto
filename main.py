import random
import itertools
from collections import deque
from pyamaze import maze, agent, textLabel, COLOR

# ============================================================
# CONFIGURAÇÕES
# ============================================================
LINHAS, COLUNAS = 10, 21
QUANTIDADE_CAIXAS = 9        # caixinhas a coletar, além do ponto de partida (0)
RETORNAR_AO_INICIO = False   # True  -> fecha o ciclo voltando à cidade 0 (TSP clássico)
                              # False -> termina na última caixinha coletada (caminho aberto)
DISTANCIA_MINIMA = 6         # nº mínimo de passos reais (dentro do labirinto) entre
                              # quaisquer duas cidades, pra elas não nascerem coladas

# ============================================================
# 1. Criação do labirinto
# ============================================================
labirinto = maze(LINHAS, COLUNAS)
labirinto.CreateMaze(loopPercent=50)

# ============================================================
# 2. BFS: menor caminho dentro do labirinto entre duas células
# ============================================================
def buscar_caminho_bfs(mapa, inicio, fim):
    fila = deque([(inicio, "")])
    visitados = {inicio}

    while fila:
        atual, caminho_str = fila.popleft()
        if atual == fim:
            return caminho_str, len(caminho_str)

        for direcao, livre in mapa[atual].items():
            if livre == 1:
                r, c = atual
                if direcao == 'E': prox = (r, c + 1)
                elif direcao == 'W': prox = (r, c - 1)
                elif direcao == 'N': prox = (r - 1, c)
                elif direcao == 'S': prox = (r + 1, c)

                if prox not in visitados:
                    visitados.add(prox)
                    fila.append((prox, caminho_str + direcao))
    return "", float('inf')

# ============================================================
# 3. Sorteio das cidades (0 = início, 1..9 = caixinhas), garantindo
#    que fiquem espalhadas: distância real (em passos) >= DISTANCIA_MINIMA
# ============================================================
todas_celulas = [(r, c) for r in range(1, LINHAS + 1) for c in range(1, COLUNAS + 1)]

def sortear_cidades_espalhadas(quantidade, dist_minima, tentativas=500):
    for _ in range(tentativas):
        candidatas = random.sample(todas_celulas, quantidade)
        ok = True
        for i in range(len(candidatas)):
            for j in range(i + 1, len(candidatas)):
                _, dist = buscar_caminho_bfs(labirinto.maze_map, candidatas[i], candidatas[j])
                if dist < dist_minima:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            return candidatas
    # se não achou uma combinação perfeita, devolve a última tentativa
    # (evita loop infinito em labirintos pequenos/valor de DISTANCIA_MINIMA alto demais)
    return candidatas

coordenadas_cidades = sortear_cidades_espalhadas(QUANTIDADE_CAIXAS + 1, DISTANCIA_MINIMA)

# ============================================================
# 4. Matriz de distâncias entre todas as cidades
# ============================================================
N = QUANTIDADE_CAIXAS + 1
distancias = {i: {} for i in range(N)}
for i in range(N):
    for j in range(N):
        if i != j:
            distancias[i][j] = buscar_caminho_bfs(
                labirinto.maze_map, coordenadas_cidades[i], coordenadas_cidades[j]
            )
        else:
            distancias[i][j] = ("", 0)

# ============================================================
# 5. Caixeiro Viajante por força bruta (rota sempre começa fixa em 0)
# ============================================================
menor_comprimento = float('inf')
melhor_rota_sequencia = []
melhor_caminho_agente = ""

for permutacao in itertools.permutations(range(1, N)):
    rota_atual = [0] + list(permutacao)
    if RETORNAR_AO_INICIO:
        rota_atual = rota_atual + [0]

    custo_total = 0
    caminho_total_str = ""
    for i in range(len(rota_atual) - 1):
        origem, destino = rota_atual[i], rota_atual[i + 1]
        caminho_str, dist = distancias[origem][destino]
        custo_total += dist
        caminho_total_str += caminho_str

    if custo_total < menor_comprimento:
        menor_comprimento = custo_total
        melhor_rota_sequencia = rota_atual
        melhor_caminho_agente = caminho_total_str

print(f"Melhor sequência de visitação: {melhor_rota_sequencia}")
print(f"Menor quantidade de passos totais: {menor_comprimento}")

# ============================================================
# 6. Visualização
# ============================================================
# Marca cada caixinha no labirinto com um agente parado (não se move sozinho,
# fica só como "pino" na posição). Início em verde, caixinhas em amarelo.
for i, (r, c) in enumerate(coordenadas_cidades):
    cor = COLOR.green if i == 0 else COLOR.yellow
    agent(labirinto, x=r, y=c, shape='square', color=cor, filled=True)

textLabel(labirinto, 'Ordem de visita', melhor_rota_sequencia)
textLabel(labirinto, 'Total de passos', menor_comprimento)

# Agente que efetivamente percorre a rota ótima encontrada
inicio_x, inicio_y = coordenadas_cidades[0]
viajante = agent(labirinto, x=inicio_x, y=inicio_y, footprints=True, color=COLOR.red)
labirinto.tracePath({viajante: melhor_caminho_agente}, delay=50)

labirinto.run()
