import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from Global.puzzle_graph import PuzzleGraph
from dotenv import load_dotenv
import os

def drop_all():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    with graph.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def drop_puzzle(puzzle_name):
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    with graph.driver.session() as session:
        session.run("MATCH (p:Puzzle {name: $name}) DETACH DELETE p", name=puzzle_name)

def drop_orphan_pieces():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    graph = PuzzleGraph(uri, user, password)
    with graph.driver.session() as session:
        session.run("""
            MATCH (piece:Piece)
            WHERE NOT (:Puzzle)-[:HAS]->(piece)
            DETACH DELETE piece
        """)

name = input("Ingrese el nombre del rompecabezas que desea eliminar: ")
if name == "*":
    drop_all()
    print("Todas las entidades han sido eliminadas de la base de datos.")
else:
    drop_puzzle(name)
    drop_orphan_pieces()
    print(f"El rompecabezas '{name}' ha sido eliminado de la base de datos.")