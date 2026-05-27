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

from unicodedata import name

from neo4j import GraphDatabase

class PuzzleGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_puzzle(self, name, num_pieces):
        with self.driver.session() as session:
            session.run("CREATE (p:Puzzle {name: $name, num_pieces: $num_pieces})", name=name, num_pieces=num_pieces)

    def create_piece(self, puzzle_name, piece_index, section, description):
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Puzzle {name: $puzzle_name})
                CREATE (p)-[:HAS]->(piece:Piece {index: $piece_index, section: $section, description: $description})
            """, puzzle_name=puzzle_name, piece_index=piece_index, section=section, description=description)

    def connect_pieces(self, piece_index1, piece_index2, direction):
        with self.driver.session() as session:
            session.run("""
                MATCH (p1:Piece {index: $piece_index1}), (p2:Piece {index: $piece_index2})
                CREATE (p1)-[:CONNECTED_TO {direction: $direction}]->(p2)
            """, piece_index1=piece_index1, piece_index2=piece_index2, direction=direction)

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
                RETURN piece.id AS piece_id, piece.section AS section, r.direction AS direction, connected_piece.id AS connected_piece_id, piece.missing AS missing
            """, puzzle_name=puzzle_name)
            return [record.data() for record in result]