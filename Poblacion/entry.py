import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Global.puzzle_graph import PuzzleGraph
from dotenv import load_dotenv
import os

def create_new_puzzle():
    print("Aquí puedes crear un nuevo rompecabezas. Por favor, ingresa el nombre del rompecabezas y el número de piezas.")
    name = input("Nombre del rompecabezas: ")
    num_pieces = None
    while not num_pieces:
        try:
            num_pieces = int(input("Número de piezas: "))
        except ValueError:
            print("Número de piezas inválido. Por favor, ingresa un número entero.")
            return
    
    try:
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        graph = PuzzleGraph(uri, user, password)
        graph.create_puzzle(name, num_pieces)
        print(f"Rompecabezas '{name}' con {num_pieces} piezas creado exitosamente.")
    except Exception as e:
        print(f"Error al crear el rompecabezas: {e}")
    
    Sections = int(input("Ingrese cuantas secciones tiene el rompecabezas: "))
    
    for i in range(1, num_pieces + 1):
        print(f"Creando pieza {i} de {num_pieces}.")
        description = input(f"Descripción de la pieza {i}: ")
        section = None
        while not section:
            try:
                section = int(input(f"Sección de la pieza {i} (1-{Sections}): "))
                if section < 1 or section > Sections:
                    print(f"Sección inválida. Por favor, ingresa un número entre 1 y {Sections}.")
                    section = None
            except ValueError:
                print("Sección inválida. Por favor, ingresa un número entero.")
        
        graph.create_piece(name, i, section, description)
        print(f"Pieza {i} creada exitosamente.")
    print("Todas las piezas creadas. Ahora puedes conectar las piezas entre sí.")
    for i in range(1, num_pieces + 1):
        while True:
            connect = input(f"Con qué piezas está conectada la pieza {i}? Ingresa los índices de las piezas conectadas separados por comas (o deja en blanco si no hay conexiones): ")
            if connect.strip():
                connections = connect.split(",")
                try:
                    connections = [int(c.strip()) for c in connections]
                    for c in connections:
                        if c < 1 or c > num_pieces:
                            print(f"Índice de pieza inválido: {c}. Por favor, ingresa índices entre 1 y {num_pieces}.")
                            raise ValueError
                except ValueError:
                    print("Entrada inválida. Por favor, ingresa índices de piezas separados por comas.")
                    continue
                for c in connections:
                    direction = None
                    while not direction:
                        try:
                            print(f"Direcciones posibles: 1=arriba, 2=arriba-derecha, 3=derecha, 4=abajo-derecha, 5=abajo, 6=abajo-izquierda, 7=izquierda, 8=arriba-izquierda")
                            direction = int(input(f"Dirección de la conexión entre la pieza {i} y la pieza {c} (1-8): "))
                            if direction < 1 or direction > 8:
                                print("Dirección inválida. Por favor, ingresa un número entre 1 y 8.")
                                direction = None
                        except ValueError:
                            print("Dirección inválida. Por favor, ingresa un número entero.")
                    graph.connect_pieces(name, i, c, direction)
                    print(f"Pieza {i} conectada a pieza {c} en dirección {direction}.")
                break
            else:
                break
    print("Rompecabezas creado exitosamente con todas las piezas y conexiones.")

    
create_new_puzzle()