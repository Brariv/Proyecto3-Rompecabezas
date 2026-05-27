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


drop_all()  
print("Todas las entidades han sido eliminadas de la base de datos.")