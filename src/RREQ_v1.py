import simpy
import random
import math


class Node:
    def __init__(self, env, node_id, x, y, coverage_radius):
        self.env = env
        self.node_id = node_id
        self.x = x
        self.y = y
        self.coverage_radius = coverage_radius
        self.neighbors = []

        #estructuras AODV
        self.routing_table = {}  #dest_id -> {'next_hop': id, 'hops': n}
        self.broadcast_id = 0
        self.seen_rreqs = set()  #(origen_id, bcast_id). Conjunto de tuplas para almacenar el historial de mensajes RREQ enviados


    def calculate_neighbors(self, all_nodes):
            self.neighbors = []
            for other_node in all_nodes:
                if self.node_id != other_node.node_id:
                    dist = math.hypot(self.x - other_node.x, self.y - other_node.y)
                    if dist <= self.coverage_radius:
                        self.neighbors.append(other_node)

    #tyransmision
    def broadcast(self, packet):
        """Envia una copia del paquete a todos los vecinos."""
        for neighbor in self.neighbors:
            self.env.process(self.transmit(packet.copy(), neighbor))

    def transmit(self, packet, receiver):
        """Simula un pequenio retraso en el aire antes de que el vecino reciba el paquete."""
        yield self.env.timeout(0.1)
        receiver.receive(packet)

    def receive(self, packet):
        """Procesa los paquetes entrantes."""
        if packet['type'] == 'RREQ':
            self.handle_rreq(packet)

    #bsuqueda de ruta
    def initiate_route_discovery(self, dest_id):
        self.broadcast_id += 1
        packet = {
            'type': 'RREQ',
            'src': self.node_id,
            'dest': dest_id,
            'bcast_id': self.broadcast_id,
            'hop_count': 0,
            'last_hop': self.node_id
        }
        print(f"\n[{self.env.now:.1f}] *** NODO {self.node_id} INICIA BUSQUEDA hacia NODO {dest_id} ***")
        self.seen_rreqs.add((self.node_id, self.broadcast_id))
        self.broadcast(packet)

    def handle_rreq(self, packet):
        rreq_identifier = (packet['src'], packet['bcast_id'])

        #ignorar RREQ repetidos
        if rreq_identifier in self.seen_rreqs:
            return
        self.seen_rreqs.add(rreq_identifier)

        #reverse route
        sender = packet['last_hop']
        hops_to_src = packet['hop_count'] + 1

        if packet['src'] not in self.routing_table or self.routing_table[packet['src']]['hops'] > hops_to_src:
            self.routing_table[packet['src']] = {'next_hop': sender, 'hops': hops_to_src}

        print(f"[{self.env.now:.1f}] Nodo {self.node_id:02d} recibio RREQ de origen {packet['src']} via Nodo {sender} (Saltos: {hops_to_src})")

        #es el destino final?
        if packet['dest'] == self.node_id:
            print(f"  -> DESTINO ENCONTRADO! El Nodo {self.node_id} ya sabe que esta a {hops_to_src} saltos del Nodo {packet['src']}.")
        else:
            #no es destino final, continua transmtiendo sobre la red
            new_packet = packet.copy()
            new_packet['hop_count'] = hops_to_src
            new_packet['last_hop'] = self.node_id
            self.broadcast(new_packet)


def setup_network(num_nodes=20, area_size=100, coverage_radius=35):
    env = simpy.Environment()
    nodes = []


    random.seed(42) #usamos una semilla para tener reproducividad en ejercicio.

    for i in range(num_nodes):
        x = random.uniform(0, area_size)
        y = random.uniform(0, area_size)
        nodes.append(Node(env, i, x, y, coverage_radius))

    for node in nodes:
        node.calculate_neighbors(nodes)

    return env, nodes


if __name__ == "__main__":
    env, red_nodos = setup_network(num_nodes=20, area_size=100, coverage_radius=35)

    #proceso que espera 1.0 y luego inicia la busqueda desde el nodo 0 hacia el 19
    def start_discovery(env, nodes, src_id, dest_id):
        yield env.timeout(1.0)
        nodes[src_id].initiate_route_discovery(dest_id)

    env.process(start_discovery(env, red_nodos, 0, 19))

    env.run(until=5)
    print("\n¡Simulacion finalizada!")