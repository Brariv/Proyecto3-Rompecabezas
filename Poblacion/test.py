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
    graph.connect_pieces(1, 2, 3)  # piece 1 connected to piece 2 to the right
    graph.connect_pieces(2, 3, 5)  # piece 2 connected to piece 3 down
    graph.connect_pieces(3, 4, 3)  # piece 3 connected to piece 4 to the right
    graph.connect_pieces(4, 1, 5)  # piece 4 connected to piece 1 down

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


drop_all()  
test_puzzle_graph()
test_get_puzzles()
