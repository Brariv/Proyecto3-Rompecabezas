# Proyecto3-Rompecabezas

Sistema de gestión y armado de rompecabezas sobre Neo4j. Almacena cada rompecabezas como un grafo de piezas conectadas y genera instrucciones paso a paso para armarlo, incluso cuando hay piezas faltantes.

---

## Estructura del proyecto

```
Proyecto3-Rompecabezas/
├── Global/
│   ├── puzzle_graph.py   # Capa de acceso a Neo4j (PuzzleGraph)
│   └── dropdb.py         # Utilidad para eliminar datos de la BD
├── Poblacion/
│   ├── entry.py          # CLI para cargar un nuevo rompecabezas
│   └── manual.md         # Manual de uso de entry.py
├── Solver/
│   └── main.py           # CLI principal: selección, armado y pasos
├── .env                  # Credenciales Neo4j (no versionar)
└── README.md
```

---

## Requisitos

- Python 3.10+
- Neo4j Aura (o instancia local)
- Dependencias Python:

```bash
pip install neo4j python-dotenv
```

### Archivo `.env`

```
NEO4J_URI=neo4j+s://<host>.databases.neo4j.io
NEO4J_USERNAME=<usuario>
NEO4J_PASSWORD=<contraseña>
```

---

## Modelo de datos en Neo4j

```
                  ┌──────────────────────────┐
                  │         :Puzzle          │
                  │  name:        STRING     │
                  │  num_pieces:  INT        │
                  └───┬──────┬──────┬────────┘
                      │      │      │
                   :HAS   :HAS   :HAS
                      │      │      │
                      ▼      ▼      ▼
               ┌────────┐ ┌────────┐ ┌────────┐
               │ :Piece │ │ :Piece │ │ :Piece │  ...
               │ index  │ │ index  │ │ index  │
               │ section│ │ section│ │ section│
               │ desc.  │ │ desc.  │ │ desc.  │
               │ missing│ │ missing│ │ missing│
               └───┬────┘ └────────┘ └───┬────┘
                   │                     │
                   └──── :CONNECTED_TO ──┘
                         { direction: INT }
```

### Nodos

| Label | Propiedad | Tipo | Descripción |
|-------|-----------|------|-------------|
| `:Puzzle` | `name` | STRING | Identificador único del rompecabezas |
| `:Puzzle` | `num_pieces` | INT | Total de piezas |
| `:Piece` | `index` | INT | Número de la pieza dentro del rompecabezas |
| `:Piece` | `section` | INT | Sección a la que pertenece (default: 1) |
| `:Piece` | `description` | STRING | Descripción visual para identificación física |
| `:Piece` | `missing` | BOOLEAN | `true` si la pieza está faltante |

### Relaciones

| Relación | Dirección | Descripción |
|----------|-----------|-------------|
| `:HAS` | `(Puzzle)→(Piece)` | El rompecabezas contiene esta pieza |
| `:CONNECTED_TO` | `(Piece)→(Piece)` | Dos piezas se ensamblan físicamente. Tiene propiedad `direction` (1-8) |

### Brújula de direcciones

```
        8   1   2
         ↖  ↑  ↗
      7 ←  [ ]  → 3
         ↙  ↓  ↘
        6   5   4
```

| Valor | Dirección | Recíproco |
|-------|-----------|-----------|
| 1 | Norte    | 5 |
| 2 | Noreste  | 6 |
| 3 | Este     | 7 |
| 4 | Sureste  | 8 |
| 5 | Sur      | 1 |
| 6 | Suroeste | 2 |
| 7 | Oeste    | 3 |
| 8 | Noroeste | 4 |

---

## Módulos

### `Global/puzzle_graph.py` — PuzzleGraph

Capa de acceso a Neo4j. Todas las demás partes del sistema la importan.

| Método | Descripción |
|--------|-------------|
| `create_puzzle(name, num_pieces)` | Crea o actualiza un nodo `:Puzzle` |
| `create_piece(puzzle_name, index, section, description)` | Crea o actualiza una pieza y la conecta al rompecabezas con `:HAS` |
| `connect_pieces(puzzle_name, index1, index2, direction)` | Crea o actualiza una relación `:CONNECTED_TO` entre dos piezas |
| `get_puzzles()` | Retorna todos los rompecabezas con `name`, `total_pieces`, `num_sections` |
| `get_puzzle_pieces_by_section(puzzle_name)` | Retorna `{sección: [piezas]}` ordenado |
| `get_available_pieces(puzzle_name)` | Retorna piezas no faltantes ordenadas por sección e índice |
| `list_missing_pieces(puzzle_name)` | Retorna piezas con `missing = true` |
| `get_piece_from_puzzle(puzzle_name, index)` | Retorna una pieza específica |
| `get_connected_pieces(puzzle_name, index)` | Retorna los vecinos de una pieza con dirección |
| `get_puzzle_graph(puzzle_name)` | Retorna el grafo completo de un rompecabezas |
| `reset_all_missing()` | Resetea `missing = false` en todas las piezas de la BD |
| `set_all_pieces_not_missing(puzzle_name)` | Resetea `missing = false` en un rompecabezas |
| `set_missing_piece(puzzle_name, index)` | Alterna `missing` de una sola pieza |
| `mark_missing_pieces(puzzle_name, indices)` | Marca una lista de índices como faltantes |
| `get_assembly_sequence(puzzle_name, start_index)` | Ejecuta BFS y retorna la secuencia de armado |

#### `get_assembly_sequence` — detalle

Implementa un BFS sobre `:CONNECTED_TO` (tratado como no dirigido) con las siguientes reglas:

```
1. Empieza en start_index dentro de la sección S
2. Recorre S completamente (atravesando piezas faltantes)
3. Salta a S+1, S+2, ... (secciones mayores en orden ascendente)
4. Luego S-1, S-2, ... (secciones menores en orden descendente)
5. Dentro de cada nueva sección, empieza en la pieza de menor índice disponible
```

Cada paso retorna:

```json
{
  "step": 1,
  "piece_index": 4,
  "section": 1,
  "description": "...",
  "is_missing": false,
  "connects_with": [
    { "neighbor_index": 3, "neighbor_description": "...", "direction": 3 }
  ]
}
```

---

### `Poblacion/entry.py` — Carga de rompecabezas

CLI interactivo para ingresar un rompecabezas completo a la BD.

```bash
python Poblacion/entry.py
```

Flujo:

```
Nombre del rompecabezas  →  create_puzzle()
Número de secciones
Para cada pieza:
  Descripción + Sección  →  create_piece()
  Conexiones + Dirección →  connect_pieces()
```

Las conexiones se declaran desde la pieza origen hacia la pieza destino. La dirección representa hacia dónde queda la pieza destino respecto a la origen.

Ver [Poblacion/manual.md](Poblacion/manual.md) para ejemplos detallados.

---

### `Solver/main.py` — Armado interactivo

CLI principal del sistema. Conecta con Neo4j, guía al usuario por el armado completo e imprime la secuencia paso a paso.

```bash
python Solver/main.py
```

Flujo de la sesión:

```
┌──────────────────────────────────────────────────┐
│         Sistema de Armado de Rompecabezas        │
└──────────────────────┬───────────────────────────┘
                       │
           reset_all_missing()          ← limpia estado anterior
                       │
           select_puzzle()              ← lista rompecabezas disponibles
                       │
           get_puzzle_pieces_by_section()
           show_puzzle_info()           ← muestra piezas por sección
                       │
           handle_missing_pieces()      ← opcional: marcar faltantes
           mark_missing_pieces()
                       │
           select_start_piece()         ← elige pieza inicial
           get_available_pieces()
                       │
           get_assembly_sequence()      ← BFS desde pieza inicial
                       │
           print_solution()             ← imprime pasos numerados
                       │
           ¿Armar otro? (s/n)
```

Ejemplo de salida:

```
==================================================
  Secuencia de armado: Caracol
==================================================

Paso 1: Colocar pieza 4 (cuerpo morado izquierdo). Pieza inicial.

Paso 2: [HUECO] La pieza 5 (cuerpo morado del caracol) está faltante.
        Si estuviera, se ensamblaría al Norte de pieza 4 (cuerpo morado izquierdo).

Paso 3: Colocar pieza 6 (cuerpo azul oscuro superior).
        Se ensambla al Norte de pieza 5 (cuerpo morado del caracol).

--------------------------------------------------
=== Fin del armado ===
Piezas ensambladas: 9 de 10
Piezas faltantes: 1 (índices [5])
--------------------------------------------------
```

---

### `Global/dropdb.py` — Utilidad de limpieza

```bash
python Global/dropdb.py
```

| Entrada | Acción |
|---------|--------|
| `*` | Elimina todos los nodos y relaciones de la BD |
| `<nombre>` | Elimina ese rompecabezas y sus piezas; luego borra piezas huérfanas |

---

## Ejecución rápida

```bash
# 1. Cargar un rompecabezas
python Poblacion/entry.py

# 2. Armar un rompecabezas
python Solver/main.py

# 3. Limpiar la BD
python Global/dropdb.py
```

---

## Notas de diseño

- Las relaciones `:CONNECTED_TO` son físicamente dirigidas en Neo4j pero el solver las trata como **no dirigidas** (`-[:CONNECTED_TO]-`). La dirección recíproca se calcula con `((d - 1 + 4) % 8) + 1`.
- `MERGE` en lugar de `CREATE` garantiza que recargar el mismo rompecabezas no genera duplicados.
- El BFS atraviesa piezas faltantes en lugar de detenerse, para que piezas del "otro lado" de un hueco sigan siendo accesibles en la secuencia.
