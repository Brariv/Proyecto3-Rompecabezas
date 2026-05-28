import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Global.puzzle_graph import PuzzleGraph
from dotenv import load_dotenv

#Constantes de brújula
DIR_NAMES = {
    1: "Norte", 2: "Noreste", 3: "Este",  4: "Sureste",
    5: "Sur",   6: "Suroeste", 7: "Oeste", 8: "Noroeste",
}

SEPARATOR_HEAVY = "=" * 50
SEPARATOR_LIGHT = "-" * 50

def header(title: str):
    print(f"\n{SEPARATOR_HEAVY}")
    print(f"  {title}")
    print(SEPARATOR_HEAVY)

def ask(prompt: str) -> str:
    return input(f"\n{prompt}").strip()


def ask_int(prompt: str):
    user_input = ask(prompt)
    try:
        return int(user_input)
    except ValueError:
        return None

#Seleccionar rompecabezas a armar
def select_puzzle(graph) -> str | None:
    puzzles = graph.get_puzzles()
    if not puzzles:
        print("No hay rompecabezas cargados en la base de datos.")
        return None

    print("\nRompecabezas disponibles:")
    for option_number, puzzle in enumerate(puzzles, 1):
        if puzzle["num_sections"] > 1:
            print(f"  {option_number}) {puzzle['name']:<22} ({puzzle['total_pieces']} piezas, {puzzle['num_sections']} secciones)")
        else:
            print(f"  {option_number}) {puzzle['name']:<22} ({puzzle['total_pieces']} piezas)")

    while True:
        user_input = ask(f"Seleccione un rompecabezas (1-{len(puzzles)}) o escriba el nombre: ")
        if user_input.isdigit():
            selected_index = int(user_input) - 1
            if 0 <= selected_index < len(puzzles):
                return puzzles[selected_index]["name"]
        else:
            name_matches = [puzzle for puzzle in puzzles if puzzle["name"].lower() == user_input.lower()]
            if name_matches:
                return name_matches[0]["name"]
        print(f"  Entrada inválida. Ingrese un número del 1 al {len(puzzles)} o el nombre exacto.")

#Mostrar info del rompecabezas
def show_puzzle_info(sections: dict, puzzle_name: str, total_pieces: int):
    print(f"\nHas seleccionado: {puzzle_name} ({total_pieces} piezas)")
    print("\n[NOTA] Se asume que las secciones van ordenadas de izquierda a derecha.")

    if len(sections) == 1:
        piece_indices = [piece["index"] for piece in list(sections.values())[0]]
        print(f"Piezas disponibles: {piece_indices}")
    else:
        for section_number in sorted(sections.keys()):
            piece_indices = [piece["index"] for piece in sections[section_number]]
            print(f"  Sección {section_number}: {piece_indices}")

#Marcar piezas faltantes
def handle_missing_pieces(graph, puzzle_name: str, all_indices: set) -> list:
    response = ask("¿Hay piezas faltantes? (s/n): ").lower()
    if response != "s":
        return []

    while True:
        user_input = ask(
            "Ingrese los índices de las piezas faltantes separados por coma\n"
            "(ej. 3,7,9) o presione Enter para omitir:\n> "
        )
        if not user_input:
            return []

        index_strings = [part.strip() for part in user_input.split(",")]
        parsed_indices = []
        has_error = False
        for index_str in index_strings:
            if not index_str.isdigit():
                print(f"  Entrada inválida: '{index_str}'. Ingrese solo números separados por coma.")
                has_error = True
                break
            piece_index = int(index_str)
            if piece_index not in all_indices:
                print(f"  La pieza {piece_index} no existe en el rompecabezas '{puzzle_name}'.")
                has_error = True
                break
            parsed_indices.append(piece_index)

        if has_error:
            continue

        marked_pieces = graph.mark_missing_pieces(puzzle_name, parsed_indices)
        print("\nPiezas marcadas como faltantes:")
        for marked_piece in marked_pieces:
            print(f"  - Pieza {marked_piece['marked']}: {marked_piece['description']}")
        return parsed_indices

#Selección de pieza inicial
def select_start_piece(graph, puzzle_name: str, all_indices: set, missing_set: set):
    available_pieces = graph.get_available_pieces(puzzle_name)

    if not available_pieces:
        print("  No hay piezas disponibles para armar.")
        return None

    print("\nPiezas disponibles para iniciar el armado:")
    for piece in available_pieces:
        missing_neighbors = sorted(piece.get("missing_neighbors") or [])
        if not missing_neighbors:
            missing_suffix = ""
        elif len(missing_neighbors) == 1:
            missing_suffix = f"  [pieza {missing_neighbors[0]} está faltante]"
        else:
            neighbors_joined = ", ".join(str(neighbor_index) for neighbor_index in missing_neighbors)
            missing_suffix = f"  [piezas {neighbors_joined} están faltantes]"
        print(f"  {piece['index']:>3}) {piece['description']}{missing_suffix}")

    available_indices = {piece["index"] for piece in available_pieces}

    while True:
        chosen_index = ask_int("Ingrese el índice de la pieza por la que desea comenzar: ")
        if chosen_index is None:
            print("  Entrada inválida. Ingrese un número.")
            continue
        if chosen_index in missing_set:
            print(f"  La pieza {chosen_index} está marcada como faltante. Elija otra pieza inicial.")
            continue
        if chosen_index not in all_indices:
            print(f"  La pieza {chosen_index} no existe en el rompecabezas '{puzzle_name}'.")
            continue
        if chosen_index not in available_indices:
            print(f"  La pieza {chosen_index} no está disponible.")
            continue
        return chosen_index

#Imprimir pasos
def print_solution(steps: list, puzzle_name: str):
    header(f"Secuencia de armado: {puzzle_name}")

    placed_count    = sum(1 for step in steps if not step["is_missing"])
    missing_indices = [step["piece_index"] for step in steps if step["is_missing"]]

    previous_section = None
    for step in steps:
        piece_index   = step["piece_index"]
        description   = step["description"]
        is_missing    = step["is_missing"]
        connections   = step["connects_with"]
        step_number   = step["step"]
        section       = step["section"]

        # Etiqueta para raíces de BFS (piezas sin conexiones previas)
        if not connections:
            if step_number == 1:
                root_label = "Pieza inicial elegida por el usuario."
            elif section != previous_section:
                root_label = f"Inicio de la Sección {section}."
            else:
                root_label = f"Inicio de un componente nuevo dentro de la Sección {section}."
        else:
            root_label = None

        if is_missing:
            print(f"\nPaso {step_number}: [HUECO] La pieza {piece_index} ({description}) está faltante.")
            if root_label:
                print(f"        {root_label}")
            if connections:
                for connection in connections:
                    direction_name = DIR_NAMES.get(connection["direction"], str(connection["direction"]))
                    print(f"        Si estuviera, se ensamblaría al {direction_name} de pieza {connection['neighbor_index']} ({connection['neighbor_description']}).")
        else:
            if not connections:
                print(f"\nPaso {step_number}: Colocar pieza {piece_index} ({description}). {root_label}")
            else:
                connection_parts = " y ".join(
                    f"al {DIR_NAMES.get(connection['direction'], connection['direction'])} de pieza {connection['neighbor_index']} ({connection['neighbor_description']})"
                    for connection in connections
                )
                print(f"\nPaso {step_number}: Colocar pieza {piece_index} ({description}).")
                print(f"        Se ensambla {connection_parts}.")

        previous_section = section

    print(f"\n{SEPARATOR_LIGHT}")
    print("=== Fin del armado ===")
    print(f"Piezas ensambladas: {placed_count} de {len(steps)}")
    if missing_indices:
        print(f"Piezas faltantes: {len(missing_indices)} (índices {missing_indices})")
    else:
        print("¡Rompecabezas completo!")
    print(SEPARATOR_LIGHT)


#Main
def main():
    load_dotenv()
    neo4j_uri      = os.getenv("NEO4J_URI")
    neo4j_username = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    try:
        graph = PuzzleGraph(neo4j_uri, neo4j_username, neo4j_password)
        graph.driver.verify_connectivity()
    except Exception as connection_error:
        print(f"No se pudo conectar a la base de datos. Verifique el servicio.\n{connection_error}")
        return

    header("Sistema de Armado de Rompecabezas")

    while True:
        # 1. Reset is_missing de corridas anteriores
        graph.reset_all_missing()

        # 2. Seleccionar rompecabezas
        puzzle_name = select_puzzle(graph)
        if not puzzle_name:
            break

        # 3. Info del rompecabezas
        sections   = graph.get_puzzle_pieces_by_section(puzzle_name)
        all_pieces = [piece for section_pieces in sections.values() for piece in section_pieces]
        if not all_pieces:
            print(f"  El rompecabezas '{puzzle_name}' no tiene piezas cargadas.")
            continue

        total_pieces = sum(len(section_pieces) for section_pieces in sections.values())
        all_indices  = {piece["index"] for piece in all_pieces}

        show_puzzle_info(sections, puzzle_name, total_pieces)

        # 4. Marcar piezas faltantes
        missing_list = handle_missing_pieces(graph, puzzle_name, all_indices)
        missing_set  = set(missing_list)

        # 5. Seleccionar pieza inicial
        start_index = select_start_piece(graph, puzzle_name, all_indices, missing_set)
        if start_index is None:
            continue

        # 6. Ejecutar BFS y mostrar pasos
        print(f"\nCalculando secuencia de armado desde pieza {start_index}...")
        steps = graph.get_assembly_sequence(puzzle_name, start_index)

        if not steps:
            print("  No se pudo generar la secuencia de armado.")
        else:
            print_solution(steps, puzzle_name)

        # 7. Continuar o salir
        continue_response = ask("¿Desea armar otro rompecabezas? (s/n): ").lower()
        if continue_response != "s":
            break

    graph.close()
    print("\nHasta luego.\n")


main()
