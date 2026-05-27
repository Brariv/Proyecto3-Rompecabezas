import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Global.puzzle_graph import PuzzleGraph
from dotenv import load_dotenv

#Constantes de brújula
DIR_NAMES = {
    1: "Norte", 2: "Noreste", 3: "Este",  4: "Sureste",
    5: "Sur",   6: "Suroeste", 7: "Oeste", 8: "Noroeste",
}

SEP       = "=" * 50
SEP_LIGHT = "-" * 50

def header(title: str):
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)

def ask(prompt: str) -> str:
    return input(f"\n{prompt}").strip()


def ask_int(prompt: str):
    raw = ask(prompt)
    try:
        return int(raw)
    except ValueError:
        return None

#Seleccionar rompecabezas a armar
def select_puzzle(graph) -> str | None:
    puzzles = graph.get_puzzles()
    if not puzzles:
        print("No hay rompecabezas cargados en la base de datos.")
        return None

    print("\nRompecabezas disponibles:")
    for i, pz in enumerate(puzzles, 1):
        if pz["num_sections"] > 1:
            print(f"  {i}) {pz['name']:<22} ({pz['total_pieces']} piezas, {pz['num_sections']} secciones)")
        else:
            print(f"  {i}) {pz['name']:<22} ({pz['total_pieces']} piezas)")

    while True:
        raw = ask(f"Seleccione un rompecabezas (1-{len(puzzles)}) o escriba el nombre: ")
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(puzzles):
                return puzzles[idx]["name"]
        else:
            match = [pz for pz in puzzles if pz["name"].lower() == raw.lower()]
            if match:
                return match[0]["name"]
        print(f"  Entrada inválida. Ingrese un número del 1 al {len(puzzles)} o el nombre exacto.")

#Mostrar info del rompecabezas
def show_puzzle_info(sections: dict, puzzle_name: str, total_pieces: int):
    print(f"\nHas seleccionado: {puzzle_name} ({total_pieces} piezas)")
    print("\n[NOTA] Se asume que las secciones van ordenadas de izquierda a derecha.")

    if len(sections) == 1:
        indices = [p["index"] for p in list(sections.values())[0]]
        print(f"Piezas disponibles: {indices}")
    else:
        for sec_num in sorted(sections.keys()):
            indices = [p["index"] for p in sections[sec_num]]
            print(f"  Sección {sec_num}: {indices}")

#Marcar piezas faltantes
def handle_missing_pieces(graph, puzzle_name: str, all_indices: set) -> list:
    resp = ask("¿Hay piezas faltantes? (s/n): ").lower()
    if resp != "s":
        return []

    while True:
        raw = ask(
            "Ingrese los índices de las piezas faltantes separados por coma\n"
            "(ej. 3,7,9) o presione Enter para omitir:\n> "
        )
        if not raw:
            return []

        parts = [p.strip() for p in raw.split(",")]
        parsed = []
        error = False
        for part in parts:
            if not part.isdigit():
                print(f"  Entrada inválida: '{part}'. Ingrese solo números separados por coma.")
                error = True
                break
            n = int(part)
            if n not in all_indices:
                print(f"  La pieza {n} no existe en el rompecabezas '{puzzle_name}'.")
                error = True
                break
            parsed.append(n)

        if error:
            continue

        marked = graph.mark_missing_pieces(puzzle_name, parsed)
        print("\nPiezas marcadas como faltantes:")
        for m in marked:
            print(f"  - Pieza {m['marked']}: {m['description']}")
        return parsed

#Selección de pieza inicial
def select_start_piece(graph, puzzle_name: str, all_indices: set, missing_set: set):
    available = graph.get_available_pieces(puzzle_name)

    if not available:
        print("  No hay piezas disponibles para armar.")
        return None

    print("\nPiezas disponibles para iniciar el armado:")
    for p in available:
        print(f"  {p['index']:>3}) {p['description']}")

    if missing_set:
        print(f"\n  (Piezas faltantes: {sorted(missing_set)})")

    available_indices = {p["index"] for p in available}

    while True:
        val = ask_int("Ingrese el índice de la pieza por la que desea comenzar: ")
        if val is None:
            print("  Entrada inválida. Ingrese un número.")
            continue
        if val in missing_set:
            print(f"  La pieza {val} está marcada como faltante. Elija otra pieza inicial.")
            continue
        if val not in all_indices:
            print(f"  La pieza {val} no existe en el rompecabezas '{puzzle_name}'.")
            continue
        if val not in available_indices:
            print(f"  La pieza {val} no está disponible.")
            continue
        return val

#Imprimir pasos
def print_solution(steps: list, puzzle_name: str):
    header(f"Secuencia de armado: {puzzle_name}")

    placed_count    = sum(1 for s in steps if not s["is_missing"])
    missing_indices = [s["piece_index"] for s in steps if s["is_missing"]]

    for step in steps:
        idx     = step["piece_index"]
        desc    = step["description"]
        missing = step["is_missing"]
        conns   = step["connects_with"]
        num     = step["step"]

        if missing:
            print(f"\nPaso {num}: [HUECO] La pieza {idx} ({desc}) está faltante.")
            if conns:
                for c in conns:
                    dir_name = DIR_NAMES.get(c["direction"], str(c["direction"]))
                    print(f"        Si estuviera, se ensamblaría al {dir_name} de pieza {c['neighbor_index']} ({c['neighbor_description']}).")
        else:
            if not conns:
                print(f"\nPaso {num}: Colocar pieza {idx} ({desc}). Pieza inicial.")
            else:
                conn_parts = " y ".join(
                    f"al {DIR_NAMES.get(c['direction'], c['direction'])} de pieza {c['neighbor_index']} ({c['neighbor_description']})"
                    for c in conns
                )
                print(f"\nPaso {num}: Colocar pieza {idx} ({desc}).")
                print(f"        Se ensambla {conn_parts}.")

    print(f"\n{SEP_LIGHT}")
    print("=== Fin del armado ===")
    print(f"Piezas ensambladas: {placed_count} de {len(steps)}")
    if missing_indices:
        print(f"Piezas faltantes: {len(missing_indices)} (índices {missing_indices})")
    else:
        print("¡Rompecabezas completo!")
    print(SEP_LIGHT)


#Main
def main():
    load_dotenv()
    uri      = os.getenv("NEO4J_URI")
    user     = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    try:
        graph = PuzzleGraph(uri, user, password)
        graph.driver.verify_connectivity()
    except Exception as e:
        print(f"No se pudo conectar a la base de datos. Verifique el servicio.\n{e}")
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
        all_pieces = [p for sec in sections.values() for p in sec]
        if not all_pieces:
            print(f"  El rompecabezas '{puzzle_name}' no tiene piezas cargadas.")
            continue

        total_pieces = sum(len(v) for v in sections.values())
        all_indices  = {p["index"] for p in all_pieces}

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
        again = ask("¿Desea armar otro rompecabezas? (s/n): ").lower()
        if again != "s":
            break

    graph.close()
    print("\nHasta luego.\n")


if __name__ == "__main__":
    main()