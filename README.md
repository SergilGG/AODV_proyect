# Simulación de Eventos Discretos: Protocolo de Enrutamiento AODV

Este repositorio contiene la implementación de un simulador de eventos discretos para el protocolo de enrutamiento reactivo **AODV** (Ad-hoc On-Demand Distance Vector), diseñado para redes inalámbricas Ad-hoc (MANETs). 

El proyecto fue desarrollado como parte de la evaluación del Examen de Conocimientos Generales (EGC) para la Maestría en Ciencias de la Computación e Ingeniería.

## Descripción del Proyecto

El objetivo principal es aislar la capa de red (Capa 3 del modelo OSI), abstrayendo la capa MAC y el medio físico, para evaluar de manera pura la lógica de descubrimiento, establecimiento de rutas y reenvío de datos (forwarding). 

El proyecto consta de dos componentes principales:
1. **Motor de Simulación (`simulador_aodv.py`):** Construido sobre la biblioteca `SimPy`, maneja la concurrencia y el tiempo simulado para el intercambio de paquetes de control (HELLO, RREQ, RREP) y de datos (DATA).
2. **Visualizador Topológico (`visualizador_aodv.py`):** Una herramienta gráfica construida con `Tkinter` para validar matemáticamente el modelo espacial y la distancia euclidiana entre los nodos.

## Características Implementadas

* **Topología Estática y Reproducible:** 20 nodos distribuidos pseudoaleatoriamente en un área de 100x100 usando una semilla fija (42).
* **Mantenimiento de Vecindad:** Emisión periódica concurrente de mensajes `HELLO`.
* **Descubrimiento de Ruta Reactivo:** Inundación de la red con paquetes `RREQ` mitigando colisiones mediante memoria caché (`seen_rreqs`).
* **Establecimiento de Ruta:** Generación de rutas reversas y directas unicast mediante paquetes `RREP`.
* **Transmisión de Datos:** Reenvío descentralizado de estructuras de datos anidadas comprobando el *Happy Path*.
* **Prevención de Bucles:** Manejo de excepciones y caídas de paquetes al intentar enrutar hacia nodos físicamente aislados.

## Instalación y Uso

### Prerrequisitos
Se necesita tener Python 3.10 instalado. La única dependencia externa es `simpy`.

```bash
pip install simpy