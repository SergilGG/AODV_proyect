import tkinter as tk
import random
import math


#======== HARD CODE ============
num_nodes = 20
area_size = 100
coverage_radius = 35
seed = 42

#happy path de 0 a 19:
calculated_route = [0, 3, 12, 19]
isolate_node = 16

#======================================================


scale_ = 6
tk_windows_size = area_size * scale_ + 100  #con margenes


class VisualizadorRed:
    def __init__(self, master):
        self.master = master
        self.master.title("Topologia AODV")

        self.canvas = tk.Canvas(master, width=tk_windows_size, height=tk_windows_size, bg="white")
        self.canvas.pack(padx=20, pady=20)

        self.nodos = []
        self.generar_nodos()
        self.draw_network()

    def generar_nodos(self):
        """Recrea las coordenadas exactas usando la misma semilla."""
        random.seed(seed)
        for id_nodo in range(num_nodes):
            x = random.uniform(0, area_size)
            y = random.uniform(0, area_size)
            self.nodos.append({'id': id_nodo, 'x': x, 'y': y})

    def neighbors(self, nodo1, nodo2):
        """Calcula si estan dentro del radio de cobertura."""
        dist = math.hypot(nodo1['x'] - nodo2['x'], nodo1['y'] - nodo2['y']) #distancia euclidiana
        return dist <= coverage_radius

    def coord_transform(self, valor):
        """Escala las coordenadas y aniade un margen."""
        return valor * scale_ + 50

    def draw_network(self):
        #dibujar todas las conexiones fisicas
        for i in range(len(self.nodos)):
            for j in range(i + 1, len(self.nodos)):
                if self.neighbors(self.nodos[i], self.nodos[j]):
                    x1, y1 = self.coord_transform(self.nodos[i]['x']), self.coord_transform(self.nodos[i]['y'])
                    x2, y2 = self.coord_transform(self.nodos[j]['x']), self.coord_transform(self.nodos[j]['y'])
                    self.canvas.create_line(x1, y1, x2, y2, fill="#808080", dash=(4, 4)) #808080 gris

        #dibujar la Ruta Exitosa
        for i in range(len(calculated_route) - 1):
            nodo_actual = self.nodos[calculated_route[i]]
            siguiente_nodo = self.nodos[calculated_route[i + 1]]

            x1, y1 = self.coord_transform(nodo_actual['x']), self.coord_transform(nodo_actual['y'])
            x2, y2 = self.coord_transform(siguiente_nodo['x']), self.coord_transform(siguiente_nodo['y'])

            #dirección del paquete DATA
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=3, arrow=tk.LAST)

        #dibujar nodos
        r = 12  #radio del nodo
        for nodo in self.nodos:
            cx, cy = self.coord_transform(nodo['x']), self.coord_transform(nodo['y'])

            color_fondo = "lightblue"
            color_texto = "black"
            grosor_borde = 1

            #nodos clave
            if nodo['id'] == 0:
                color_fondo = "green"  #ORIGEN
                color_texto = "white"
                grosor_borde = 3
            elif nodo['id'] == 19:
                color_fondo = "blue"  #DESTINO
                color_texto = "white"
                grosor_borde = 3
            elif nodo['id'] in calculated_route:
                color_fondo = "orange"  #NODOS INTERMEDIOS DE LA RUTA
            elif nodo['id'] == isolate_node:
                color_fondo = "black"  #NODO AISLADO (prueba 2)
                color_texto = "white"

            #dibujar el circulo
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color_fondo, width=grosor_borde)
            #dibujar el ID del nodo en el centro
            self.canvas.create_text(cx, cy, text=str(nodo['id']), fill=color_texto, font=("Arial", 10, "bold"))

        self.canvas.create_text(100, 20, text="Verde: Origen (0)", fill="green", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 40, text="Azul: Destino (19)", fill="blue", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 60, text="Rojo: Ruta DATA", fill="red", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 80, text="Negro: Nodo aislado (16)", fill="black", font=("Arial", 12, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizadorRed(root)
    root.mainloop()