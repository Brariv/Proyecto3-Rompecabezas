import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Global.puzzle_graph import PuzzleGraph
from dotenv import load_dotenv
import os

def test_puzzle_graph():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    # Initialize the PuzzleGraph
    graph = PuzzleGraph(uri, user, password)

    # Create a puzzle
    graph.create_puzzle("Test Puzzle", 4)
    # Create pieces for the puzzle
    graph.create_piece("Test Puzzle", 1, 1, "Piece 1 description")
    graph.create_piece("Test Puzzle", 2, 1, "Piece 2 description")
    graph.create_piece("Test Puzzle", 3, 2, "Piece 3 description")
    graph.create_piece("Test Puzzle", 4, 2, "Piece 4 description")
    # Connect pieces
    graph.connect_pieces("Test Puzzle", 1, 2, 3)  # piece 1 connected to piece 2 to the right
    graph.connect_pieces("Test Puzzle", 2, 3, 5)  # piece 2 connected to piece 3 down
    graph.connect_pieces("Test Puzzle", 3, 4, 3)  # piece 3 connected to piece 4 to the right
    graph.connect_pieces("Test Puzzle", 4, 1, 5)  # piece 4 connected to piece 1 down

def test_get_puzzles():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    puzzles = graph.get_puzzles()
    print(puzzles)
    puzzle = graph.get_puzzle_graph("Test Puzzle")
    print(puzzle)

def drop_all():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    with graph.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def set_missing_piece():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    graph.set_missing_piece("Test Puzzle", 2)

def get_piece_from_puzzle():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    piece = graph.get_piece_from_puzzle("Test Puzzle", 2)
    print(piece)

def get_connections_from_piece():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    connections = graph.get_connected_pieces("Test Puzzle", 2)
    print(connections)

def list_all_missing_pieces():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    missing_pieces = graph.list_missing_pieces("Test Puzzle")
    print(missing_pieces)

def set_all_pieces_not_missing():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    graph.set_all_pieces_not_missing("Test Puzzle")

def get_puzzle_graph():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    puzzle_graph = graph.get_puzzle_graph("Test Puzzle")
    print(puzzle_graph)

def test_reset_all_missing():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    graph.reset_all_missing()
    missing = graph.list_missing_pieces("Test Puzzle")
    print("missing after reset:", missing)

def test_mark_missing_pieces():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    marked = graph.mark_missing_pieces("Test Puzzle", [2, 3])
    print("marked as missing:", marked)
    missing = graph.list_missing_pieces("Test Puzzle")
    print("missing pieces:", missing)

def test_get_available_pieces():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    available = graph.get_available_pieces("Test Puzzle")
    print("available pieces:", available)

def test_get_puzzle_pieces_by_section():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    sections = graph.get_puzzle_pieces_by_section("Test Puzzle")
    print("pieces by section:", sections)

def test_assembly_sequence():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    sequence = graph.get_assembly_sequence("Test Puzzle", 1)
    print("assembly sequence:")
    for step in sequence:
        flag = " [MISSING]" if step["is_missing"] else ""
        print(f"  Step {step['step']}: piece {step['piece_index']}{flag} — {step['description']} | connects_with={step['connects_with']}")

# drop_all()
# test_puzzle_graph()
test_reset_all_missing()
test_mark_missing_pieces()
test_get_available_pieces()
test_get_puzzle_pieces_by_section()
set_missing_piece()
get_piece_from_puzzle()
get_connections_from_piece()
test_get_puzzles()
list_all_missing_pieces()
set_all_pieces_not_missing()
get_puzzle_graph()
test_assembly_sequence()
