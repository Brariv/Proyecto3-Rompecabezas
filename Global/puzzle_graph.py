# neo4j structure for puzzle graph
# (puzzle)-[:HAS]->(piece)
# (piece)-[:CONNECTED_TO]->(piece)
# (piece)-[:CONNECTED_TO]->(piece)
# (piece)-[:CONNECTED_TO]->(piece)

# puzzle has properties:
# - name: name of the puzzle
# - num_pieces: number of pieces in the puzzle INT


# piece has properties:
# - index: unique identifier for the piece INT
# - section: the section of the puzzle it belongs to (e.g. "1", "2", "3", "4") INT

# relationships:
# - HAS: connects a puzzle to its pieces
# - CONNECTED_TO: connects pieces that are connected in the puzzle
#    - CONNECTED_TO relationships can have properties:
#    - direction: the direction of the connection (e.g. "up", "down", "left", "right"), this would be represented by a number between 1 to 8
#.     - where: 1 for up, 2 for up-right, 3 for right, 4 for down-right, 5 for down, 6 for down-left, 7 for left, 8 for up-left

from collections import deque
from neo4j import GraphDatabase

class PuzzleGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_puzzle(self, name, num_pieces):
        with self.driver.session() as session:
            session.run("MERGE (p:Puzzle {name: $name}) SET p.num_pieces = $num_pieces", name=name, num_pieces=num_pieces)

    def create_piece(self, puzzle_name, piece_index, section, description):
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})
                MERGE (p)-[:HAS]->(piece:Piece {index: $piece_index})
                SET piece.section = $section, piece.description = $description
            """, puzzle_name=puzzle_name, piece_index=piece_index, section=section, description=description)

    def connect_pieces(self, puzzle_name, piece_index1, piece_index2, direction):
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece1:Piece {index: $piece_index1}), (p)-[:HAS]->(piece2:Piece {index: $piece_index2})
                MERGE (piece1)-[r:CONNECTED_TO]->(piece2)
                SET r.direction = $direction
            """, puzzle_name=puzzle_name, piece_index1=piece_index1, piece_index2=piece_index2, direction=direction)

    def get_puzzles(self):
        with self.driver.session() as session:
            result = session.run("MATCH (p:Puzzle) RETURN id(p) AS id")
            return [record["id"] for record in result]

    def set_missing_piece(self, puzzle_name, piece_index):
        with self.driver.session() as session:
            # toggle missing: if true -> false, if false or null -> true
            session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece {index: $piece_index})
                SET piece.missing = NOT(coalesce(piece.missing, false))
            """, puzzle_name=puzzle_name, piece_index=piece_index)

    def get_puzzle_graph(self, puzzle_name):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                OPTIONAL MATCH (piece)-[r:CONNECTED_TO]->(connected_piece:Piece)
                RETURN piece.id AS piece_id, piece.section AS section, r.direction AS direction, connected_piece.id AS connected_piece_id, piece.description AS description, piece.missing AS missing
            """, puzzle_name=puzzle_name)
            return [record.data() for record in result]

    def get_piece_from_puzzle(self, puzzle_name, piece_index):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece {index: $piece_index})
                RETURN piece.id AS piece_id, piece.section AS section, piece.description AS description, piece.missing AS missing
            """, puzzle_name=puzzle_name, piece_index=piece_index)
            return [record.data() for record in result]
        
    def get_connected_pieces(self, puzzle_name, piece_index):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece {index: $piece_index})
                OPTIONAL MATCH (piece)-[r:CONNECTED_TO]->(connected_piece:Piece)
                RETURN connected_piece.id AS connected_piece_id, connected_piece.section AS section, r.direction AS direction, connected_piece.description AS description, connected_piece.missing AS missing
            """, puzzle_name=puzzle_name, piece_index=piece_index)
            return [record.data() for record in result]
        
    def list_missing_pieces(self, puzzle_name):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                WHERE piece.missing = true
                RETURN piece.id AS piece_id, piece.section AS section, piece.description AS description
            """, puzzle_name=puzzle_name)
            return [record.data() for record in result]
    
    def set_all_pieces_not_missing(self, puzzle_name):
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                SET piece.missing = false
            """, puzzle_name=puzzle_name)

    def reset_all_missing(self):
        with self.driver.session() as session:
            session.run("MATCH (piece:Piece) SET piece.missing = false")

    def mark_missing_pieces(self, puzzle_name, indexes):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                WHERE piece.index IN $indexes
                SET piece.missing = true
                RETURN piece.index AS marked, piece.description AS description
            """, puzzle_name=puzzle_name, indexes=indexes)
            return [record.data() for record in result]

    def get_available_pieces(self, puzzle_name):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                WHERE NOT piece.missing
                RETURN piece.index AS index, piece.section AS section, piece.description AS description
                ORDER BY piece.section, piece.index
            """, puzzle_name=puzzle_name)
            return [record.data() for record in result]

    def get_puzzle_pieces_by_section(self, puzzle_name):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                RETURN piece.index AS index, piece.section AS section, piece.description AS description
                ORDER BY piece.section, piece.index
            """, puzzle_name=puzzle_name)
            sections = {}
            for record in result:
                sec = record["section"]
                if sec not in sections:
                    sections[sec] = []
                sections[sec].append(record.data())
            return sections

    def get_assembly_sequence(self, puzzle_name, start_index):
        with self.driver.session() as session:
            pieces_result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                RETURN piece.index AS index, piece.section AS section,
                       piece.description AS description, piece.missing AS missing
            """, puzzle_name=puzzle_name)
            pieces = {r["index"]: dict(r) for r in pieces_result}

            conn_result = session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})-[:HAS]->(piece:Piece)
                MATCH (piece)-[r:CONNECTED_TO]-(neighbor:Piece)
                RETURN piece.index AS from_index, neighbor.index AS to_index,
                       CASE WHEN startNode(r) = piece THEN r.direction
                            ELSE ((r.direction - 1 + 4) % 8) + 1 END AS direction
            """, puzzle_name=puzzle_name)
            adjacency = {idx: [] for idx in pieces}
            for r in conn_result:
                adjacency[r["from_index"]].append((r["to_index"], r["direction"]))

        sections = {}
        for idx, piece in pieces.items():
            sec = piece["section"]
            if sec not in sections:
                sections[sec] = []
            sections[sec].append(idx)
        for sec in sections:
            sections[sec].sort()

        start_section = pieces[start_index]["section"]
        all_sections = sorted(sections.keys())
        higher = [s for s in all_sections if s > start_section]
        lower = sorted([s for s in all_sections if s < start_section], reverse=True)
        section_order = [start_section] + higher + lower

        visited = set()
        steps = []

        def bfs_from(start_idx):
            queue = deque([start_idx])
            while queue:
                idx = queue.popleft()
                if idx in visited:
                    continue
                visited.add(idx)
                piece = pieces[idx]
                connects_with = [
                    {
                        "neighbor_index": nb,
                        "neighbor_description": pieces[nb]["description"],
                        "direction": direction,
                    }
                    for nb, direction in adjacency[idx]
                    if nb in visited
                ]
                steps.append({
                    "step": len(steps) + 1,
                    "piece_index": idx,
                    "section": piece["section"],
                    "description": piece["description"],
                    "is_missing": piece["missing"] or False,
                    "connects_with": connects_with,
                })
                for nb, _ in adjacency[idx]:
                    if nb not in visited:
                        queue.append(nb)

        for section in section_order:
            sec_pieces = sections.get(section, [])
            if section == start_section:
                sec_start = start_index
            else:
                available = [i for i in sec_pieces if not (pieces[i].get("missing") or False)]
                sec_start = min(available) if available else (min(sec_pieces) if sec_pieces else None)

            if sec_start is not None and sec_start not in visited:
                bfs_from(sec_start)

            for idx in sec_pieces:
                if idx not in visited:
                    bfs_from(idx)

        return steps