from itertools import chain
from typing import List, Dict, Any, Literal

from fastapi import FastAPI, HTTPException, Depends
from neo4j import GraphDatabase, Session

ELEMENT_ID = "element_id"  # name of the id-property passed to the client (element_id in neo4j)
DB_INIT_FILE = "ExerciseGraphDB_SS2023.cypher"  # file to initialize the database
app = FastAPI(title="Exercise GraphDB", version="0.1.0", docs_url="/")
db = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "password"))


def _unpack(nodes) -> List:
    """ helper to unpack a list of lists of nodes into a single list of nodes. add ids and types to the nodes """
    nodes = list(chain(*nodes))
    for n in nodes:
        if hasattr(n, "id"):  # this has to be "element_id", a magic string from neo4j
            n._properties[ELEMENT_ID] = n.id  # noqa E501
        if hasattr(n, "labels") and len(n.labels) == 1:  # add node type too, so the all node endpoint is more useful
            n._properties["type"] = next(iter(n.labels))  # noqa E501
    return nodes


# initialize before app startup. don't use app.on_event("startup") because swagger doc types  have to be created before
with db.session() as session_:
    # always reset the database to the initial state
    with open(DB_INIT_FILE) as f:
        session_.run("MATCH (n) DETACH DELETE n")
        session_.run(f.read())
        print("Created database")
    # dynamically create literal (exact matching) types so fastapi can validate inputs
    NodeType = Literal[tuple(_unpack(_unpack(session_.run("MATCH (n) RETURN distinct labels(n)"))))]  # noqa
    RelType = Literal[tuple(_unpack(session_.run("MATCH ()-[r]->() RETURN distinct type(r)")))]  # noqa


def sess() -> Session:
    with db.session() as s:
        yield s


@app.get("/data")
async def data(session=Depends(sess)) -> List[Dict[str, Any]]:
    return _unpack(session.run("MATCH (n) RETURN n"))


@app.get("/data/{typ}")
async def get_all_of_type(typ: NodeType, session=Depends(sess)) -> List[Dict[str, Any]]:
    return _unpack(session.run(f"MATCH (n:{typ}) RETURN n"))


@app.get("/data/{source}/{dest}")
async def get_relationship(source: NodeType, dest: NodeType, session=Depends(sess)) -> List[Dict[str, Any]]:
    result = list(session.run(f"MATCH (n:{source})-[r]-(m:{dest}) RETURN n, r, m"))
    return [{"source": node1, "target": node2, "type": rel.type, "properties": rel._properties}  # noqa E501
            for node1, rel, node2 in result]


@app.post("/node/{typ}")
async def create_node(typ: NodeType, properties: Dict[str, Any], session=Depends(sess)) -> List[Dict[str, Any]]:
    return _unpack(list(session.run(f"CREATE (n:{typ} $properties) RETURN n", properties=properties)))


@app.post("/relationship/{source}/{typ}/{dest}")
async def create_relationship(source: int, dest: int, typ: RelType, properties: Dict[str, Any], session=Depends(sess)) -> List[Dict[str, Any]]:
    return _unpack(list(session.run(f"MATCH (n), (m) WHERE id(n)=$source AND id(m)=$dest CREATE (n)-[r:{typ} $properties]->(m) RETURN r", source=source, dest=dest, properties=properties)))


@app.delete("/node/{node_id}")
async def delete_node(node_id: int, session=Depends(sess)) -> Dict[str, str]:
    node = session.run(f"MATCH (n) WHERE id(n)=$node_id RETURN n", node_id=node_id).single()
    if node is None:
        raise HTTPException(status_code=400, detail="Node not found")
    session.run(f"MATCH (n) WHERE id(n)=$node_id DETACH DELETE n", node_id=node_id)
    return {"message": "Node deleted."}


@app.delete("/relationship/{relationship_id}")
async def delete_relationship(relationship_id: int, session=Depends(sess)) -> Dict[str, str]:
    rel = session.run(f"MATCH ()-[r]-() WHERE id(r)=$relationship_id RETURN r", relationship_id=relationship_id).single(strict=False)
    if rel is None:
        raise HTTPException(status_code=400, detail="Relationship not found")
    session.run(f"MATCH ()-[r]-() WHERE id(r)=$relationship_id DELETE r", relationship_id=relationship_id)
    return {"message": "Relationship deleted."}


@app.post("/edit/node/{node_id}")
async def edit_node(node_id: int, properties: Dict[str, Any], session=Depends(sess)) -> List[Dict[str, Any]]:
    node = session.run(f"MATCH (n) WHERE id(n)=$node_id RETURN n", node_id=node_id).single()
    if node is None:
        raise HTTPException(status_code=400, detail="Node not found")
    return _unpack(list(session.run(f"MATCH (n) WHERE id(n)=$node_id SET n+=$properties RETURN n", node_id=node_id, properties=properties)))
