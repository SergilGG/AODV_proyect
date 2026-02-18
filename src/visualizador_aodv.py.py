import tkinter as tk
import random
import math

# ======== HARD CODE ============
num_nodes = 20
area_size = 100
coverage_radius = 35
seed = 42

#happy path de 0 a 19:
calculated_route = [0, 3, 12, 19]
isolate_node = 16

#======================================================

scale_ = 6
tk_windows_size = area_size * scale_ + 100  # con margenes


class VisualizadorRed:
    def __init__(self, master):
        self.master = master
        self.master.title("Topologia AODV")


        frame_botones = tk.Frame(master)
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Imagen 0: Radios de Cobertura", command=self.mostrar_imagen_0, bg="lightgray").pack(side=tk.LEFT, padx=10)
        tk.Button(frame_botones, text="Imagen 1: Conexiones Fisicas", command=self.mostrar_imagen_1, bg="lightgray").pack(side=tk.LEFT, padx=10)
        tk.Button(frame_botones, text="Imagen 2: Ruta Happy Path", command=self.mostrar_imagen_2, bg="lightgray").pack(side=tk.LEFT, padx=10)
        # =========================================================

        self.canvas = tk.Canvas(master, width=tk_windows_size, height=tk_windows_size, bg="white")
        self.canvas.pack(padx=20, pady=20)

        self.nodos = []
        self.generar_nodos()

        self.mostrar_imagen_0()

    def generar_nodos(self):
        """Recrea las coordenadas exactas usando la misma semilla."""
        random.seed(seed)
        for id_nodo in range(num_nodes):
            x = random.uniform(0, area_size)
            y = random.uniform(0, area_size)
            self.nodos.append({'id': id_nodo, 'x': x, 'y': y})

    def neighbors(self, nodo1, nodo2):
        """Calcula si estan dentro del radio de cobertura."""
        dist = math.hypot(nodo1['x'] - nodo2['x'], nodo1['y'] - nodo2['y'])  # distancia euclidiana
        return dist <= coverage_radius

    def coord_transform(self, valor):
        """Escala las coordenadas y aniade un margen."""
        return valor * scale_ + 50


    def draw_grid(self):
        """Dibuja una cuadricula"""
        step = 10
        inicio = self.coord_transform(0)
        fin = self.coord_transform(area_size)

        for i in range(0, area_size + step, step):
            coord = self.coord_transform(i)
            #lineas verticales y horizontales muy tenues
            self.canvas.create_line(coord, inicio, coord, fin, fill="#f0f0f0", dash=(2, 2))
            self.canvas.create_line(inicio, coord, fin, coord, fill="#f0f0f0", dash=(2, 2))

            #etiquetas numéricas en los bordes
            if i % 20 == 0:
                self.canvas.create_text(coord, fin + 15, text=str(i), fill="gray", font=("Arial", 8))
                self.canvas.create_text(inicio - 15, coord, text=str(i), fill="gray", font=("Arial", 8))

    def draw_coverage(self):
        """Dibuja el radio de alcance de cada antena."""
        r_scaled = coverage_radius * scale_
        for nodo in self.nodos:
            cx, cy = self.coord_transform(nodo['x']), self.coord_transform(nodo['y'])

            color_cobertura = "#d9e6f2" #azul

            if nodo['id'] == isolate_node:
                color_cobertura = "#ffcccc"  #rojo

            self.canvas.create_oval(cx - r_scaled, cy - r_scaled, cx + r_scaled, cy + r_scaled, outline=color_cobertura, dash=(6, 4))

    def draw_physical_connections(self):
        """Dibuja todas las conexiones fisicas en gris 808080"""
        for i in range(len(self.nodos)):
            for j in range(i + 1, len(self.nodos)):
                if self.neighbors(self.nodos[i], self.nodos[j]):
                    x1, y1 = self.coord_transform(self.nodos[i]['x']), self.coord_transform(self.nodos[i]['y'])
                    x2, y2 = self.coord_transform(self.nodos[j]['x']), self.coord_transform(self.nodos[j]['y'])
                    self.canvas.create_line(x1, y1, x2, y2, fill="#808080", dash=(6, 6)) #amarillo

    def draw_happy_path(self):
        """Dibuja la ruta exitosa en rojo"""
        for i in range(len(calculated_route) - 1):
            nodo_actual = self.nodos[calculated_route[i]]
            siguiente_nodo = self.nodos[calculated_route[i + 1]]

            x1, y1 = self.coord_transform(nodo_actual['x']), self.coord_transform(nodo_actual['y'])
            x2, y2 = self.coord_transform(siguiente_nodo['x']), self.coord_transform(siguiente_nodo['y'])

            #direccion del paquete DATA
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=3, arrow=tk.LAST)

    def draw_nodes(self):
        """Dibuja circulos y los IDs de los nodos"""
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
                color_fondo = "black"  #NODO AISLADO
                color_texto = "white"

            #dibujar el circulo
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=color_fondo, width=grosor_borde)
            #dibujar el ID del nodo en el centro
            self.canvas.create_text(cx, cy, text=str(nodo['id']), fill=color_texto, font=("Arial", 10, "bold"))

    def draw_labels(self):
        """Dibuja la leyenda en la esquina superior izquierda"""
        self.canvas.create_text(100, 20, text="Verde: Origen (0)", fill="green", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 40, text="Azul: Destino (19)", fill="blue", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 60, text="Rojo: Ruta DATA", fill="red", font=("Arial", 12, "bold"))
        self.canvas.create_text(100, 80, text="Negro: Nodo aislado (16)", fill="black", font=("Arial", 12, "bold"))



    def mostrar_imagen_0(self):
        """Imagen 0: Solo Cobertura"""
        self.canvas.delete("all") # Limpiamos el lienzo
        self.draw_grid()
        self.draw_coverage()
        self.draw_nodes()
        self.draw_labels()

    def mostrar_imagen_1(self):
        """Imagen 1: Solo Conexiones"""
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_physical_connections()
        self.draw_nodes()
        self.draw_labels()

    def mostrar_imagen_2(self):
        """Imagen 2: Ruta Happy Path"""
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_physical_connections()
        self.draw_happy_path()
        self.draw_nodes()
        self.draw_labels()


if __name__ == "__main__":
    root = tk.Tk()
    app = VisualizadorRed(root)
    root.mainloop()