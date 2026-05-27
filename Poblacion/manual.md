# Manual de Población — `entry.py`

Este script es una interfaz de línea de comandos (CLI) para cargar un nuevo rompecabezas en la base de datos Neo4j. Guía al usuario paso a paso para crear el nodo del rompecabezas, sus piezas y las conexiones físicas entre ellas.

---

## Flujo de ejecución

```
┌─────────────────────────────────────────────────────┐
│                    entry.py                         │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────┐
         │  Nombre del rompecabezas│  ← input del usuario
         │  Número de piezas       │  ← input del usuario
         └────────────┬────────────┘
                      │  graph.create_puzzle(name, num_pieces)
                      ▼
         ┌─────────────────────────┐
         │  Número de secciones    │  ← input del usuario
         └────────────┬────────────┘
                      │
                      │  Para cada pieza i = 1 .. num_pieces:
                      ▼
         ┌─────────────────────────┐
         │  Descripción de pieza i │  ← input del usuario
         │  Sección de pieza i     │  ← input del usuario (1..Sections)
         └────────────┬────────────┘
                      │  graph.create_piece(name, i, section, description)
                      ▼
         ┌─────────────────────────┐
         │  ¿Con qué piezas        │
         │  conecta la pieza i?    │  ← índices separados por coma
         │  Dirección de cada      │
         │  conexión (1-8)         │  ← input del usuario
         └────────────┬────────────┘
                      │  graph.connect_pieces(name, i, c, direction)
                      ▼
         ┌─────────────────────────┐
         │  Rompecabezas creado    │
         │  exitosamente           │
         └─────────────────────────┘
```

---

## Ejemplo de conexion entre piezas

```

                         ____
                        /\  __\_
                       /  \/ \___\
                       \     /___/
                    /\_/     \    \
                   /     2    \____\
               ___/\       _  /    /
              / \/  \     /_\/____/
              \     /     \___\
              /     \_/\  /   /
             /    1     \/___/
             \  _       /   /
              \/_|     /___/
                 /     \___\
                 \  /\_/___/
                  \/___/

                                    [n4biS]
```
En este caso las conexiones de la pieza 1 son: ninguna porque este recibe las conexiones desde las piezas 2. 
La pieza 2 conecta con la pieza 1 en dirección 5 (sur/abajo) o 6 (suroeste/abajo a la izquierda).

entonces al programa preguntar (Siguiendo este ejemplo):
```
Con qué piezas está conectada la pieza 1? Ingresa los índices de las piezas conectadas separados por comas (o deja en blanco si no hay conexiones):
*SE DEJA VACIO*

Con qué piezas está conectada la pieza 1? Ingresa los índices de las piezas conectadas separados por comas (o deja en blanco si no hay conexiones):
*SE INGRESA 1*

Dirección de la conexión entre la pieza 2 y la pieza 1 (1-8): 
*SE INGRESA 5 o 6*
```

Explicacion: 
```
                    
               _______              _______ 
              |      _)           _|       |
              |  1  (_    and    (_    2   |      
              |_______)            |_______|

Nodo 1: Recibe conexiones desde Nodo 2, pero no declara conexiones hacia otras piezas.
Node 2: Realiza una conexion en direccion hacia de Nodo 1
Y las propiedades de la conexión se declaran desde el nodo que realiza la conexión (Nodo 2) hacia el nodo que recibe la conexión (Nodo 1) la cual es la dirección.
```
---

## Estructura generada en Neo4j

Cada ejecución exitosa produce el siguiente grafo:

```
                  ┌──────────────────────────┐
                  │         :Puzzle          │
                  │  name:       STRING      │
                  │  num_pieces: INT         │
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
               └───┬────┘ └────────┘ └───┬────┘
                   │                     │
                   └──── :CONNECTED_TO ──┘
                         { direction: INT }
```

### Nodos

| Label | Propiedad | Tipo | Descripción |
|-------|-----------|------|-------------|
| `:Puzzle` | `name` | STRING | Nombre identificador del rompecabezas |
| `:Puzzle` | `num_pieces` | INT | Total de piezas |
| `:Piece` | `index` | INT | Número de la pieza (1 .. num_pieces) |
| `:Piece` | `section` | INT | Sección a la que pertenece la pieza |
| `:Piece` | `description` | STRING | Descripción visual de la pieza |
| `:Piece` | `missing` | BOOLEAN | Si la pieza está faltante (default: false) |

### Relaciones

| Relación | Dirección | Descripción |
|----------|-----------|-------------|
| `:HAS` | `(Puzzle)→(Piece)` | El rompecabezas contiene esta pieza |
| `:CONNECTED_TO` | `(Piece)→(Piece)` | Dos piezas se ensamblan físicamente |

La propiedad `direction` en `:CONNECTED_TO` sigue la brújula de 8 puntos:

```
        8   1   2
         ↖  ↑  ↗
      7 ←  [ ]  → 3
         ↙  ↓  ↘
        6   5   4
```

| Valor | Dirección |
|-------|-----------|
| 1 | Norte (arriba) |
| 2 | Noreste |
| 3 | Este (derecha) |
| 4 | Sureste |
| 5 | Sur (abajo) |
| 6 | Suroeste |
| 7 | Oeste (izquierda) |
| 8 | Noroeste |

---

## Ejemplo de sesión

Supón un rompecabezas de 3 piezas en 1 sección:

```
Nombre del rompecabezas: Triángulo
Número de piezas: 3
Ingrese cuantas secciones tiene el rompecabezas: 1

Creando pieza 1 de 3.
Descripción de la pieza 1: esquina superior izquierda
Sección de la pieza 1 (1-1): 1

Creando pieza 2 de 3.
Descripción de la pieza 2: borde superior derecho
Sección de la pieza 2 (1-1): 1

Creando pieza 3 de 3.
Descripción de la pieza 3: base central
Sección de la pieza 3 (1-1): 1

Con qué piezas está conectada la pieza 1? 2,3
  Dirección pieza 1 → pieza 2: 3    (Este)
  Dirección pieza 1 → pieza 3: 5    (Sur)

Con qué piezas está conectada la pieza 2? (Enter — ya declarado desde pieza 1)
Con qué piezas está conectada la pieza 3? (Enter)
```

Grafo resultante:

```
  [Triángulo :Puzzle]
       │  :HAS
   ┌───┼───┐
   ▼   ▼   ▼
 [1] [2] [3]
  │    ↑   ↑
  └─3──┘   │
  └────5───┘
```

---

## Validaciones que aplica el script

| Situación | Comportamiento |
|-----------|----------------|
| `num_pieces` no es entero | Imprime error y termina (`return`) |
| Sección fuera de rango (< 1 o > Sections) | Vuelve a pedir la sección |
| Sección no es entero | Vuelve a pedir la sección |
| Índice de pieza conectada inválido | Vuelve a pedir toda la lista de conexiones |
| Dirección fuera de 1-8 | Vuelve a pedir la dirección |
| Error al conectar con Neo4j | Imprime el error (en `create_puzzle`); el script continúa con el resto del flujo |

---

## Dependencias

```
entry.py
  ├── Global/puzzle_graph.py   (PuzzleGraph — acceso a Neo4j)
  ├── python-dotenv            (carga .env)
  └── .env                     (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)
```

El script debe ejecutarse desde la raíz del proyecto:

```bash
python Poblacion/entry.py
```
