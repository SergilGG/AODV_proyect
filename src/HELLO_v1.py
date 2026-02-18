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
        self.neighbors = [] #lista de vecinos propios

        #estructuras AODV
        self.routing_table = {}  #dest_id -> {'next_hop': id, 'hops': n}
        self.broadcast_id = 0
        self.seen_rreqs = set()  #(origen_id, bcast_id). Conjunto de tuplas para almacenar el historial de mensajes RREQ enviados

        #iniciar el proceso de mensajes HELLO
        self.env.process(self.hello_worker())

    def calculate_neighbors(self, all_nodes):
        self.neighbors = []
        for other_node in all_nodes:
            if self.node_id != other_node.node_id:
                dist = math.hypot(self.x - other_node.x, self.y - other_node.y)  #se calcula area circular 'visible'
                if dist <= self.coverage_radius:  #lo que este dentro del radio de cobertura, se guarda como un vecino
                    self.neighbors.append(other_node)

    #=================================================================================
    #mensajes HELLO
    def hello_worker(self):
        """
        Envia un mensaje HELLO cada 2 segundos para avisar que aun esta vivo.
        Este proceso inicia en un t0, al inicializar los nodos
        """
        while True:
            packet = {'type': 'HELLO', 'src': self.node_id}
            #SOLO a los vecinos proximos
            for neighbor in self.neighbors:
                self.env.process(self.transmit(packet, neighbor))

            yield self.env.timeout(2.0)  #ponemos a dormir y despertamos en 2 segundos simulados para volver a mandarlo
    # =================================================================================

    def broadcast(self, packet):
        for neighbor in self.neighbors:
            self.env.process(self.transmit(packet.copy(), neighbor))

    def transmit(self, packet, receiver):
        yield self.env.timeout(0.05)  #simulamos un retraso minimo de transmision de 50ms
        receiver.receive(packet)

    def receive(self, packet):
        if packet['type'] == 'RREQ':
            self.handle_rreq(packet)
        elif packet['type'] == 'RREP':
            self.handle_rrep(packet)
        elif packet['type'] == 'HELLO':
            if packet['src'] not in self.routing_table:
                self.routing_table[packet['src']] = {'next_hop': packet['src'], 'hops': 1}

    #bpusqueda de ruta
    def initiate_route_discovery(self, dest_id):
        self.broadcast_id += 1

        # ------------------------------------------
        #paquete RREQ: {tipo, inicio de la ruta, destino final, no. de secuencia, no. latos, ultimo nodo en la ruta}
        #inicializa con 0 saltos
        packet = {
            'type': 'RREQ', 'src': self.node_id, 'dest': dest_id,
            'bcast_id': self.broadcast_id, 'hop_count': 0, 'last_hop': self.node_id
        }
        # ------------------------------------------

        print(f"[{self.env.now:0.2f}] Nodo {self.node_id} inicia busqueda hacia Nodo {dest_id}")
        self.seen_rreqs.add((self.node_id, self.broadcast_id)) #se registra el mensaje recibido. Al ser un conjunto, no hay miembros repetidos
        self.broadcast(packet) #se manda una copia del mensaje, a los vecinos inmediatos

    def handle_rreq(self, packet):
        rreq_id = (packet['src'], packet['bcast_id']) #obtenemos el id del nodoque envio el mensaje
        if rreq_id in self.seen_rreqs: return #si el mensaje ya ha sido recibido antes, termina
        self.seen_rreqs.add(rreq_id) #se aniade al conjunto del historial

        #ruta Reversa
        sender = packet['last_hop']
        hops = packet['hop_count'] + 1
        if packet['src'] not in self.routing_table or self.routing_table[packet['src']]['hops'] > hops:
            #registra el nodo envio el mensaje, para tener memorizado el camino hacia ese nodo
            self.routing_table[packet['src']] = {'next_hop': sender, 'hops': hops}

        #si el id actual (el nodo actual) es el DESTINO, termina el envio de RREQ e inicia el mensaje de regreso RREP
        if packet['dest'] == self.node_id:
            self.send_rrep(packet['src'])
        else:
            new_p = packet.copy()
            new_p['hop_count'] = hops #se suma 1 la hop_count
            new_p['last_hop'] = self.node_id #el ultimo nodo ahora es el actual
            self.broadcast(new_p) #lanza broadcast a sus vecinos conel mensaje modificado

    def send_rrep(self, target_src):
        # ------------------------------------------
        # paquete RREP: {tipo, nodoa ctual, destino final ahora es el orgien del primer RREQ, no. latos, ultimo nodo en la ruta}
        # inicializa con 0 saltos de regreso
        packet = {
            'type': 'RREP', 'src': self.node_id, 'dest': target_src,
            'hop_count': 0, 'last_hop': self.node_id
        }
        # ------------------------------------------

        #revisa la tabla de ruteo hacia el nodo origen de mensaje RREQ para saber si paso inmediato
        next_hop = self.routing_table[target_src]['next_hop']
        target_node = next((n  for n in self.neighbors if n.node_id == next_hop), None)
        if target_node:
            self.env.process(self.transmit(packet, target_node))

    def handle_rrep(self, packet):
        sender = packet['last_hop']
        hops = packet['hop_count'] + 1
        if packet['src'] not in self.routing_table or self.routing_table[packet['src']]['hops'] > hops:
            #guarda el nodo de quien se recibe el mensaje RREP para tener su tabla de ruteo hacia ese nodo
            self.routing_table[packet['src']] = {'next_hop': sender, 'hops': hops}

        if packet['dest'] == self.node_id:
            print(f"[{self.env.now:0.2f}] RUTA COMPLETADA! Nodo {self.node_id} llego al Nodo {packet['src']} en {hops} saltos.")
        else:
            new_p = packet.copy()
            new_p['hop_count'] = hops
            new_p['last_hop'] = self.node_id
            next_hop = self.routing_table[packet['dest']]['next_hop']
            target_node = next((n for n in self.neighbors if n.node_id == next_hop), None)
            if target_node:
                self.env.process(self.transmit(new_p, target_node))


def run_simulation(env, nodes, source_id, dest_id):
    yield env.timeout(1.0)  #esperamos que los HELLO dispersen sobre la red para poblar las tablas
    nodes[source_id].initiate_route_discovery(dest_id)


def setup_network(num_nodes=20, area_size=100, coverage_radius=35):
    env = simpy.Environment()
    random.seed(42)
    nodes = []
    for i in range(num_nodes):
        nodes.append(Node(env, i, random.uniform(0, area_size), random.uniform(0, area_size), coverage_radius))
    #for node in nodes: node.calculate_neighbors(nodes)

    for node in nodes:
        node.calculate_neighbors(nodes)
        neighbor_ids = [n.node_id for n in node.neighbors]
        print(f"Nodo {node.node_id:02d} posicionado en ({node.x:.1f}, {node.y:.1f}) -> Vecinos ({len(neighbor_ids)}): {neighbor_ids}")
    print('===========================================================================================================================')
    return env, nodes



if __name__ == "__main__":
    env, red = setup_network()
    env.process(run_simulation(env, red, 0, 19))
    env.run(until=15) #hasta cumplir 15 eventos/tiempos/momentos

    print("\n=========================================================================")
    nodo_origen = red[0]
    if 19 in nodo_origen.routing_table:
        ruta = nodo_origen.routing_table[19]
        print(f"EXITO: El Nodo 0 encontro al Nodo 19.")
        print(f"Siguiente salto: Nodo {ruta['next_hop']}")
        print(f"Distancia total: {ruta['hops']} saltos.")
    else:
        print("FALLO: No se encontro ruta en el tiempo establecido.")