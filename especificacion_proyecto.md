# Proyecto 03 — Elección de tecnologías de base de datos

## Especificación técnica del sistema

CC3089 Base de Datos 2 — Semestre I 2026
Universidad del Valle de Guatemala

---

## 1. Tecnología seleccionada: Neo4j

Se eligió Neo4j (base de datos orientada a grafos) por las siguientes razones:

- Un rompecabezas es naturalmente un grafo: las piezas son nodos y las conexiones físicas entre piezas son aristas.
- Cypher permite recorrer relaciones con sintaxis nativa de path traversal (`MATCH (a)-[:CONNECTS_TO]-(b)`), sin necesidad de joins recursivos como sería el caso en SQL.
- El modelo es schema-less, lo que permite agregar nuevos rompecabezas con características distintas sin modificar la estructura existente.
- El algoritmo de armado se reduce esencialmente a un BFS sobre el grafo, operación para la que Neo4j está optimizado.

### Comparación con alternativas

| Tecnología | Problema principal |
|------------|-------------------|
| SQL (PostgreSQL/MySQL) | Requeriría tabla de adyacencias con FK y consultas con CTEs recursivas (`WITH RECURSIVE`) para recorrer conexiones. Complejidad alta. |
| MongoDB (documentos) | Las conexiones entre piezas obligan a duplicar referencias o usar agregaciones complejas. No es un buen fit para grafos. |
| Redis (key-value) | No soporta consultas estructurales sobre relaciones sin índices secundarios manuales. |
| **Neo4j** | **Relaciones son ciudadanos de primera clase. Cypher tiene sintaxis nativa para path traversal.** |

---

## 2. Estructura de la base de datos

### 2.1 Nodos

#### `:Puzzle`

Representa un rompecabezas completo.

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | STRING | Identificador único del rompecabezas (ej. "Caracol", "Dinosaurio", "Zorra"). |
| `total_pieces` | INT | Cantidad total de piezas que conforman el rompecabezas. |

#### `:Piece`

Representa una pieza individual de un rompecabezas.

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `index` | INT | Número identificador de la pieza dentro del rompecabezas. Para rompecabezas no numerados (como la zorra), se asigna manualmente al cargar y se marca físicamente con masking tape. |
| `section` | INT | Número de sección a la que pertenece la pieza. Para rompecabezas multi-componente (ej. los tres animales: huevo, pollito, pájaro). Default: 1. |
| `description` | STRING | Descripción visual de la pieza para facilitar la identificación física y mejorar el feedback al usuario (ej. "cabeza amarilla del caracol con ojo", "centro verde de la espiral"). |
| `is_missing` | BOOLEAN | Indica si la pieza está marcada como faltante. Default: `false`. Se modifica desde la interfaz del usuario en runtime. |

### 2.2 Relaciones

#### `:BELONGS_TO`

Conecta cada pieza con el rompecabezas al que pertenece.

```
(:Piece)-[:BELONGS_TO]->(:Puzzle)
```

Sin propiedades. Una pieza pertenece a un único rompecabezas.

#### `:CONNECTS_TO`

Conecta dos piezas que físicamente se ensamblan entre sí.

```
(:Piece)-[:CONNECTS_TO {direction: INT}]->(:Piece)
```

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `direction` | INT | Dirección de la conexión según la tabla de brújula. Valores 1-8. |

**Tabla de brújula (valores de `direction`):**

| Valor | Dirección |
|-------|-----------|
| 1 | Norte |
| 2 | Noreste |
| 3 | Este |
| 4 | Sureste |
| 5 | Sur |
| 6 | Suroeste |
| 7 | Oeste |
| 8 | Noroeste |

**Equivalencias recíprocas** (cuando se recorre la arista en sentido inverso):

| Dirección original | Dirección recíproca |
|--------------------|---------------------|
| 1 (Norte) | 5 (Sur) |
| 2 (Noreste) | 6 (Suroeste) |
| 3 (Este) | 7 (Oeste) |
| 4 (Sureste) | 8 (Noroeste) |

**Nota sobre direccionalidad:** la relación se crea una sola vez entre cada par de piezas vecinas. En las queries se trata como no-dirigida usando `-[:CONNECTS_TO]-` (sin flecha). Si A→B tiene `direction = 3` (Este), al recorrer desde B la dirección recíproca es `7` (Oeste), y debe calcularse en el código del programa o del query.

### 2.3 Diagrama del modelo

```
                    ┌────────────────────────┐
                    │        :Puzzle         │
                    │   - name: STRING       │
                    │   - total_pieces: INT  │
                    └───────────▲────────────┘
                                │
                                │ :BELONGS_TO
                                │
                    ┌───────────┴────────────┐
                    │        :Piece          │
                    │   - index: INT         │
                    │   - section: INT       │
                    │   - description: STRING│
                    │   - is_missing: BOOL   │
                    └───────────┬────────────┘
                                │
                                │ :CONNECTS_TO
                                │ { direction: INT (1-8) }
                                ▼
                    ┌────────────────────────┐
                    │        :Piece          │
                    └────────────────────────┘
```

---

## 3. Estrategia del algoritmo de armado

### 3.1 Lógica fundamental

El algoritmo realiza un **recorrido en anchura (BFS) sobre el grafo de piezas** partiendo de la pieza inicial indicada por el usuario, siguiendo las relaciones `:CONNECTS_TO`.

**Comportamiento ante piezas faltantes:**

- El BFS **atraviesa** las piezas marcadas como `is_missing = true`.
- Cuando el recorrido encuentra una pieza faltante, **genera un paso descriptivo** indicando que hay un hueco en esa posición y con qué piezas se conectaría si estuviera presente.
- El algoritmo **continúa explorando** las piezas vecinas de la faltante a través de las CONNECTS_TO, de modo que las piezas del "otro lado" del hueco también se reportan en el armado.

Esta estrategia tiene tres ventajas clave:

1. **Refleja cómo se arma realmente un rompecabezas** (siempre extendiendo desde algo ya colocado).
2. **Aprovecha el conocimiento de adyacencias físicas** que la BD ya almacena.
3. **No deja piezas huérfanas**: incluso con piezas faltantes que aislarían geométricamente partes del rompecabezas, el algoritmo igual las visita gracias a que conoce las CONNECTS_TO a través del hueco.

### 3.2 Manejo de secciones

Para rompecabezas multi-componente (ej. tres animales, ciclo mariposa), cada sección es un subgrafo desconectado de las demás (no hay CONNECTS_TO entre piezas de secciones distintas).

El algoritmo:

1. Realiza BFS dentro de la sección donde se encuentra la pieza inicial hasta agotarla.
2. Salta a la siguiente sección numéricamente (`section + 1`) tomando como nueva "pieza inicial" la de menor índice de esa sección.
3. Repite hasta haber recorrido todas las secciones.
4. Si la pieza inicial no es de la sección 1, después de completar todas las secciones superiores vuelve a las anteriores (sección 1, 2, ...).

---

## 4. Interfaz del programa (CLI)

El programa interactúa con el usuario a través de la terminal. La lógica del flujo se gestiona en el programa; el recorrido del grafo se delega al query de Cypher (ver sección 5).

### 4.1 Flujo general de interacción

```
1. Inicio del programa y conexión a Neo4j
2. Reset de estado: SET is_missing = false en todas las piezas
3. Mostrar rompecabezas disponibles
4. Usuario selecciona rompecabezas
5. Mostrar información del rompecabezas seleccionado
6. Usuario indica piezas faltantes (si aplica)
7. Mostrar piezas disponibles para iniciar (con descripciones)
8. Usuario indica pieza inicial
9. Ejecutar query de armado
10. Mostrar pasos de armado
11. Preguntar al usuario si desea continuar o salir
```

### 4.2 Detalle de cada paso

#### Paso 1 — Inicio

El programa establece la conexión con Neo4j y muestra un mensaje de bienvenida.

```
==========================================
   Sistema de Armado de Rompecabezas
==========================================
```

#### Paso 2 — Reset de estado

Para evitar residuos de corridas anteriores, al inicio se ejecuta:

```cypher
MATCH (p:Piece)
SET p.is_missing = false
```

Esto asegura que cada sesión empiece con todas las piezas disponibles.

#### Paso 3 — Listar rompecabezas disponibles

```cypher
MATCH (pz:Puzzle)
RETURN pz.name AS name, pz.total_pieces AS total_pieces
ORDER BY pz.name
```

Mostrar al usuario:

```
Rompecabezas disponibles:
  1) Caracol           (10 piezas)
  2) Ciclo Mariposa    (14 piezas, 3 secciones)
  3) Dinosaurio        (10 piezas)
  4) Tres Animales     (13 piezas, 3 secciones)
  5) Zorra             (24 piezas)

Seleccione un rompecabezas (1-5):
```

#### Paso 4 — Selección de rompecabezas

El usuario ingresa el número o el nombre. El programa valida la entrada. Si es inválida, se vuelve a pedir.

#### Paso 5 — Mostrar información del rompecabezas

Consultar las piezas del rompecabezas con sus descripciones:

```cypher
MATCH (p:Piece)-[:BELONGS_TO]->(:Puzzle {name: $puzzle_name})
RETURN p.index AS index, p.section AS section, p.description AS description
ORDER BY p.section, p.index
```

Mostrar al usuario el rango de índices y, si hay múltiples secciones, agrupadas:

```
Has seleccionado: Tres Animales (13 piezas)
  Sección 1 (Huevo):     [1, 2, 3]
  Sección 2 (Pollito):   [4, 5, 6, 7]
  Sección 3 (Pájaro):    [8, 9, 10, 11, 12, 13]
```

Para rompecabezas de una sola sección:

```
Has seleccionado: Caracol (10 piezas)
Piezas disponibles: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

#### Paso 6 — Marcar piezas faltantes

Pregunta al usuario:

```
¿Hay piezas faltantes? (s/n):
```

Si responde `s`:

```
Ingrese los índices de las piezas faltantes separados por coma
(ej. 3,7,9) o presione Enter para omitir:
> 5,8
```

Validar que cada índice ingresado existe en el rompecabezas seleccionado. Si alguno es inválido, mostrar error y volver a pedir.

Persistir en BD:

```cypher
MATCH (p:Piece)-[:BELONGS_TO]->(:Puzzle {name: $puzzle_name})
WHERE p.index IN $missing_indices
SET p.is_missing = true
RETURN p.index AS marked, p.description AS description
```

Confirmar al usuario con descripciones:

```
Piezas marcadas como faltantes:
  - Pieza 5: cuerpo morado del caracol
  - Pieza 8: pieza azul oscuro inferior
```

#### Paso 7 — Mostrar piezas disponibles para iniciar

Listar todas las piezas no faltantes con su descripción para que el usuario pueda elegir contextualmente:

```cypher
MATCH (p:Piece)-[:BELONGS_TO]->(:Puzzle {name: $puzzle_name})
WHERE NOT p.is_missing
RETURN p.index AS index, p.section AS section, p.description AS description
ORDER BY p.section, p.index
```

Mostrar al usuario:

```
Piezas disponibles para iniciar el armado:
  1) cabeza amarilla del caracol con ojo
  2) cuerpo amarillo inferior
  3) sección naranja inferior izquierda
  4) cuerpo morado izquierdo
  6) cuerpo azul oscuro superior  [pieza 5 está faltante]
  7) cuerpo azul claro derecho
  9) centro azul oscuro inferior  [pieza 8 está faltante]
  10) centro verde de la espiral
```

#### Paso 8 — Selección de pieza inicial

Pregunta al usuario:

```
Ingrese el índice de la pieza por la que desea comenzar:
> 4
```

Validar:
- Que el índice exista en el rompecabezas.
- Que NO esté marcada como faltante.

Si la pieza inicial está marcada como faltante, mostrar error y pedir otra.

#### Paso 9 — Ejecución del query de armado

Se ejecuta la query que retorna la secuencia completa de armado (ver sección 5 para la especificación de input/output).

#### Paso 10 — Mostrar pasos

Recibir el resultado del query y mostrarlo al usuario en formato legible:

```
=== Secuencia de armado: Caracol ===

Paso 1: Colocar pieza 4 (cuerpo morado izquierdo). Pieza inicial.

Paso 2: [HUECO] La pieza 5 (cuerpo morado del caracol) está faltante.
        Si estuviera, se ensamblaría al Norte de pieza 4.

Paso 3: Colocar pieza 6 (cuerpo azul oscuro superior).
        Se ensambla al Norte del hueco donde iría pieza 5.

Paso 4: Colocar pieza 7 (cuerpo azul claro derecho).
        Se ensambla al Sur de pieza 6.

Paso 5: [HUECO] La pieza 8 (pieza azul oscuro inferior) está faltante.
        Si estuviera, se ensamblaría al Sur de pieza 7.

Paso 6: Colocar pieza 9 (centro azul oscuro inferior).
        Se ensambla al Oeste del hueco donde iría pieza 8.

Paso 7: Colocar pieza 10 (centro verde de la espiral).
        Se ensambla al Norte de pieza 9 y al Sur de pieza 6.

Paso 8: Colocar pieza 3 (sección naranja inferior izquierda).
        Se ensambla al Sur de pieza 4.

Paso 9: Colocar pieza 2 (cuerpo amarillo inferior).
        Se ensambla al Este de pieza 3.

Paso 10: Colocar pieza 1 (cabeza amarilla del caracol con ojo).
         Se ensambla al Este de pieza 2.

=== Fin del armado ===
Piezas ensambladas: 8 de 10
Piezas faltantes: 2 (índices 5 y 8)
```

#### Paso 11 — Continuar o salir

```
¿Desea armar otro rompecabezas? (s/n):
```

Si elige `s`, vuelve al paso 2 (reset de `is_missing` y selección de rompecabezas).
Si elige `n`, cerrar conexión y terminar programa.

### 4.3 Manejo de errores

| Caso | Respuesta del programa |
|------|------------------------|
| Rompecabezas inexistente | "El rompecabezas '{X}' no existe. Seleccione uno de la lista." |
| Índice de pieza fuera de rango | "La pieza {N} no existe en el rompecabezas '{X}'." |
| Pieza inicial marcada como faltante | "La pieza {N} está marcada como faltante. Elija otra pieza inicial." |
| Todas las piezas marcadas como faltantes | "No hay piezas disponibles para armar." |
| Entrada no numérica donde se esperaba número | "Entrada inválida. Ingrese un número." |
| Sin conexión a Neo4j | "No se pudo conectar a la base de datos. Verifique el servicio." |

---

## 5. Especificación del query de armado

Esta sección define lo que el query debe recibir y retornar para que el programa pueda integrarse correctamente.

### 5.1 Input del query

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `puzzle_name` | STRING | Nombre del rompecabezas a armar. |
| `start_index` | INT | Índice de la pieza inicial (debe existir y no estar marcada como faltante). |

### 5.2 Lógica esperada del algoritmo

El algoritmo debe implementar un **BFS sobre el grafo de CONNECTS_TO** con las siguientes características:

1. **Inicio**: comenzar en la pieza con `index = start_index` dentro del rompecabezas `puzzle_name`. Esta pieza forma el paso 1.

2. **Expansión**: en cada iteración, tomar todas las piezas vecinas (por `:CONNECTS_TO`) de las piezas ya visitadas que aún no se hayan visitado.

3. **Manejo de piezas faltantes (atraviesa)**:
   - Cuando el BFS encuentra una pieza con `is_missing = true`, genera un paso especial marcado como hueco (`is_missing: true` en el output).
   - El paso de hueco indica con qué piezas ya colocadas se conectaría la pieza faltante si estuviera.
   - El BFS **continúa atravesando** la pieza faltante: sus vecinas también se visitan en pasos posteriores, conectándose al "hueco" o a otras piezas presentes.

4. **Manejo de secciones (subgrafos desconectados)**:
   - Cuando se agota la sección actual (no hay más piezas vecinas disponibles ni vía huecos), saltar a la siguiente sección.
   - Tomar como nueva pieza inicial de la nueva sección la de menor índice que no esté faltante.
   - Repetir el BFS dentro de esa sección.
   - Orden de visita de secciones: primero la sección de la pieza inicial, luego las secciones con número mayor en orden ascendente, luego las secciones con número menor en orden descendente.

5. **Para cada pieza visitada (no faltante)**: identificar **con qué piezas previamente colocadas se conecta**, indicando la dirección de cada conexión.

### 5.3 Output del query

El query debe retornar una lista ordenada de pasos. Cada paso es un registro con la siguiente estructura:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `step` | INT | Número del paso (1, 2, 3, ...). |
| `piece_index` | INT | Índice de la pieza colocada (o del hueco) en este paso. |
| `section` | INT | Sección de la pieza. |
| `description` | STRING | Descripción visual de la pieza. |
| `is_missing` | BOOLEAN | `true` si esta pieza está marcada como faltante (es un hueco reportado, no una pieza ensamblada). |
| `connects_with` | LIST of `{neighbor_index: INT, neighbor_description: STRING, direction: INT}` | Lista de piezas previamente colocadas (o huecos previos) con las que se ensambla esta pieza, indicando la dirección recíproca desde el punto de vista de la pieza actual. Vacío para la pieza inicial. |

**Ejemplo de output (formato conceptual):**

```json
[
  {
    "step": 1,
    "piece_index": 4,
    "section": 1,
    "description": "cuerpo morado izquierdo",
    "is_missing": false,
    "connects_with": []
  },
  {
    "step": 2,
    "piece_index": 5,
    "section": 1,
    "description": "cuerpo morado del caracol",
    "is_missing": true,
    "connects_with": [
      {"neighbor_index": 4, "neighbor_description": "cuerpo morado izquierdo", "direction": 5}
    ]
  },
  {
    "step": 3,
    "piece_index": 6,
    "section": 1,
    "description": "cuerpo azul oscuro superior",
    "is_missing": false,
    "connects_with": [
      {"neighbor_index": 5, "neighbor_description": "cuerpo morado del caracol", "direction": 5}
    ]
  }
]
```

### 5.4 Notas para quien implementa el query

- La relación `:CONNECTS_TO` es físicamente dirigida en Neo4j pero debe tratarse como no-dirigida (usar `-[:CONNECTS_TO]-` sin flecha en los `MATCH`).
- La `direction` reportada en `connects_with` debe ser **desde el punto de vista de la pieza actual hacia la pieza vecina ya colocada**. Si la arista almacenada tiene una dirección distinta, aplicar la tabla de equivalencias recíprocas (sección 2.2).
- Las piezas con `is_missing = true` deben incluirse en el output como pasos de hueco, con su `description` y los `connects_with` correspondientes a piezas vecinas ya colocadas (que pueden ser piezas reales o huecos previos).
- El BFS debe garantizar que ninguna pieza se visite dos veces (ni piezas presentes ni huecos).
- Si la pieza inicial es de la sección N, después de agotar la sección N el algoritmo continúa con N+1, N+2, ..., y luego retrocede a N-1, N-2, ..., 1.

---

## 6. Carga inicial de datos

Los 5 rompecabezas deben poblarse en la BD antes de usar el programa. Cada rompecabezas requiere:

1. Crear el nodo `:Puzzle` con su `name` y `total_pieces`.
2. Crear todos los nodos `:Piece` con sus propiedades (`index`, `section`, `description`, `is_missing = false`).
3. Crear las relaciones `:BELONGS_TO` de cada pieza al rompecabezas.
4. Crear las relaciones `:CONNECTS_TO` entre piezas físicamente vecinas, asignando la `direction` correcta según la brújula (sección 2.2). Una sola relación por par de piezas vecinas.

**Importante para la zorra (no numerada):** asignar manualmente los índices del 1 al 24 siguiendo un orden coherente (sugerencia: fila por fila, de izquierda a derecha y de arriba a abajo). **Marcar físicamente cada pieza con masking tape** indicando su índice, para poder identificarlas durante la demostración cuando el evaluador tome una pieza al azar.

Las descripciones de cada pieza deben ser concisas pero suficientes para identificarla visualmente (ej. "esquina superior izquierda con árbol", "cara del zorro con ojos", "panda con bufanda roja").

---

## 7. Cumplimiento de la rúbrica

| Aspecto | % | Cómo se cubre |
|---------|---|---------------|
| 1. Justificación de la elección de BD | 10% | Sección 1: comparación con SQL, MongoDB, Redis. |
| 2. Diseño del modelo de datos | 20% | Sección 2: nodos, relaciones, propiedades (incluyendo `description`, `section`, `is_missing`). |
| 3. Implementación del modelo | 10% | Sección 6: carga de los 5 rompecabezas con todas sus propiedades y relaciones. |
| 4. Explicación del algoritmo | 10% | Secciones 3 y 5: BFS sobre CONNECTS_TO, manejo de secciones, atravesar piezas faltantes. |
| 5. Solución sin piezas faltantes | 20% | BFS recorre todo el grafo desde cualquier pieza inicial. |
| 6. Solución con piezas faltantes | 20% | El algoritmo atraviesa huecos y los reporta descriptivamente, no deja piezas huérfanas. |
| 7. Calidad de la presentación | 10% | Diagrama del modelo, demo en vivo con descripciones de piezas, comparación de tecnologías. |
