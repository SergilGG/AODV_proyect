import simpy
import random
import math


class Node:
    """Clase nodo"""

    def __init__(self, env, node_id, x, y, coverage_radius):
        self.env = env
        self.node_id = node_id
        self.x = x
        self.y = y
        self.coverage_radius = coverage_radius
        self.neighbors =  [] #lista para guardar los nodos que estan en rango

    def calculate_neighbors(self, all_nodes):
        """Calcula cuales nodos estan dentro de su radio de cobertura circular."""
        self.neighbors = []
        for other_node in all_nodes: #se descubren todos contra todos
            #un nodo no es vecino de si mismo
            if self.node_id != other_node.node_id:
                #distancia euclidiana en 2D
                dist = math.hypot(self.x - other_node.x, self.y - other_node.y)

                #si la distancia es menor o igual al radio, se consideran vecinos
                if dist <= self.coverage_radius:
                    self.neighbors.append(other_node)


def setup_network(num_nodes=20, area_size=100, coverage_radius=30):
    """Configura el entorno de simpy y distribuye los nodos."""
    print("=================== START =======================")
    env = simpy.Environment()
    nodes = []

    #crear los 20 nodos en posiciones (x, y) aleatorias
    for i in range(num_nodes):
        x = random.uniform(0, area_size)
        y = random.uniform(0, area_size)
        node = Node(env, node_id=i, x=x, y=y, coverage_radius=coverage_radius)
        nodes.append(node)

    #calcular los vecinos para cada nodo
    for node in nodes:
        node.calculate_neighbors(nodes)
        neighbor_ids = [n.node_id for n in node.neighbors]
        print(
            f"Nodo {node.node_id:02d} posicionado en ({node.x:.1f}, {node.y:.1f}) -> Vecinos ({len(neighbor_ids)}): {neighbor_ids}")

    return env, nodes


if __name__ == "__main__":
    #100x100 metros, radio de transmisión de 35 metros
    env, red_nodos = setup_network(num_nodes=20, area_size=100, coverage_radius=35)

    #un solo paso
    env.run(until=1)
    print("\nTopología inicializada con exito!")