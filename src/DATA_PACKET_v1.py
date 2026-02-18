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
        self.neighbors = []  #lista de vecinos propios

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
        Este proceso inicia en un t0, al inicializar los nodos.
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
            #si recibo un HELLO, ese nodo esta a 1 salto, es vecino y actualizamos tabla
            if packet['src'] not in self.routing_table:
                self.routing_table[packet['src']] = {'next_hop': packet['src'], 'hops': 1}
        elif packet['type'] == 'DATA':
            self.handle_data(packet)

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
        self.seen_rreqs.add((self.node_id, self.broadcast_id))  #se registra el mensaje recibido. Al ser un conjunto, no hay miembros repetidos
        self.broadcast(packet)  #se manda una copia del mensaje, a los vecinos inmediatos.

    def handle_rreq(self, packet):
        rreq_id = (packet['src'], packet['bcast_id'])  #obtenemos el id del nodoque envio el mensaje.
        if rreq_id in self.seen_rreqs: return  #si el mensaje ya ha sido recibido antes, termina.
        self.seen_rreqs.add(rreq_id)  #se aniade al conjunto del historial.

        #ruta inversa / reverse route
        sender = packet['last_hop']
        hops = packet['hop_count'] + 1
        if packet['src'] not in self.routing_table or self.routing_table[packet['src']]['hops'] > hops:
            #registra el nodo que envi el mensaje, para tener memorizado el camino hacia ese nodo
            self.routing_table[packet['src']] = {'next_hop': sender, 'hops': hops}

        #si el id actual (el nodo actual) es el DESTION, termina el envio de RREQ e inicia el mensaje de regreso RREP
        if packet['dest'] == self.node_id:
            self.send_rrep(packet['src'])
        else:
            new_p = packet.copy()
            new_p['hop_count'] = hops  #se suma 1 la hop_count
            new_p['last_hop'] = self.node_id  #el ultimo nodo ahora es el actual
            self.broadcast(new_p)  #lanza broadcast a sus vecinos conel mensaje modificado

    def send_rrep(self, target_src):
        # ------------------------------------------
        # paquete RREP: {tipo, nodoa ctual, destino final ahora es el orgien del primer RREQ, no. latos, ultimo nodo en la ruta}
        # inicializa con 0 saltos de regreso
        packet = {
            'type': 'RREP', 'src': self.node_id, 'dest': target_src,
            'hop_count': 0, 'last_hop': self.node_id
        }
        # ------------------------------------------

        #revisa la tabla de ruteo hacia el nodo origen del mensaje RREQ para saber que esta un paso
        next_hop = self.routing_table[target_src]['next_hop']

        target_node = next((n for n in self.neighbors if n.node_id == next_hop), None)
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
            #significa que ya conoce la ruta. Envia paquete de datos
            self.send_data(packet['src'])
        else:
            #si el nodo actual no es el destino final:
            new_p = packet.copy()
            new_p['hop_count'] = hops
            new_p['last_hop'] = self.node_id
            next_hop = self.routing_table[packet['dest']]['next_hop']
            target_node = next((n for n in self.neighbors if n.node_id == next_hop), None)
            if target_node:
                self.env.process(self.transmit(new_p, target_node))

    # ===============================================
    def send_data(self, dest_id):
        """
        Enviar un paquete usando la ruta descubierta.
        """
        #simulacion de un data
        data_packet = {
            'type': 'DATA',
            'src': self.node_id,
            'dest': dest_id,
            'payload': {
                'message': 'Hola desde el nodo origen, validando la ruta calculada.',
                'path_taken': [self.node_id]  #iniciamos una lista para registrar los nodos que toca, formando el happy path
            }
        }

        #busca en la tabla de ruteo cual es el primer paso
        next_hop = self.routing_table[dest_id]['next_hop']
        target_node = next((n for n in self.neighbors if n.node_id == next_hop), None)

        if target_node:
            print(f"[{self.env.now:0.2f}] [DATOS] Nodo {self.node_id} inicia transmision de DATOS. Siguiente salto: Nodo {next_hop}")
            self.env.process(self.transmit(data_packet, target_node))

    def handle_data(self, packet):
        """
        Tomar decisiones de reenvio en nodos intermedios.
        Funcioon que maneja el tipo de mensaje DATA en el metodo receive.
        """
        #registramos que el paquete acaba de pasar por este nodo
        packet['payload']['path_taken'].append(self.node_id)

        #si es el detino final:
        if packet['dest'] == self.node_id:
            print(f"[{self.env.now:0.2f}] EXITO DE TRANSMISION! Nodo {self.node_id} recibio el paquete de DATOS.")
            print(f"    - Mensaje: '{packet['payload']['message']}'")
            print(f"    - Ruta real recorrida: {packet['payload']['path_taken']}")
        else:
            #no soy el destino. Consulto mi tabla de ruteo para hacer reenvio
            next_hop = self.routing_table[packet['dest']]['next_hop']
            target_node = next((n for n in self.neighbors if n.node_id == next_hop), None)

            if target_node:
                print(f"[{self.env.now:0.2f}] [DATOS] Nodo {self.node_id} reenvia paquete de DATOS hacia Nodo {next_hop}")
                self.env.process(self.transmit(packet, target_node))
    # =================================================================================


#funcion para arrancar la simulacion
def run_simulation(env, nodes, source_id, dest_id):
    yield env.timeout(1.0)  #esperamos que los HELLO dispersen sobre la red para poblar las tablas
    nodes[source_id].initiate_route_discovery(dest_id)


def setup_network(num_nodes=20, area_size=100, coverage_radius=35): #no. nodos, area 'geografica', radio de covertura individual
    env = simpy.Environment()
    random.seed(42) #usamos una semilla para tener reproducividad en ejercicio.
    nodes = []
    for i in range(num_nodes):
        #instanciamos la calse Node con n nodos.
        nodes.append(Node(env, i, random.uniform(0, area_size), random.uniform(0, area_size), coverage_radius))
    #for node in nodes: node.calculate_neighbors(nodes)

    for node in nodes:
        node.calculate_neighbors(nodes)
        neighbor_ids = [n.node_id for n in node.neighbors]
        print(f"Nodo {node.node_id:02d} posicionado en ({node.x:.1f}, {node.y:.1f}) -> Vecinos ({len(neighbor_ids)}): {neighbor_ids}")
    print('===========================================================================================================================')
    return env, nodes


if __name__ == "__main__":
    env, network = setup_network()
    env.process(run_simulation(env, network, 0, 19)) #proceso de prueba, ruta de nodo 0 a nodo 19
    env.run(until=15)  #hasta cumplir 15 eventos/tiempos/momentos

    print("\n================= RUTAS =============================")
    origin_node = network[0]  #acceder al nodo 0
    dest_node = 19
    if dest_node in origin_node.routing_table:
        route = origin_node.routing_table[dest_node]  #usar destino 19
        print(f"EXITO: El Nodo 0 encontro al Nodo {dest_node}.")
        print(f"Siguiente salto inicial: Nodo {route['next_hop']}")
        print(f"Distancia total en tabla: {route['hops']} saltos.")
    else:
        print("FALLO: No se encontro ruta en el tiempo establecido.")

    # ===============================================================================
    print('===========================================================================================================================')


