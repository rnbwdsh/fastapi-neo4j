# Explanation

This is a dynamic app that can use any neo4j dataset and provide generic CRUD operations for it. It is based on FastAPI and Neo4j.
Only nodes and relations of existing types can be created, but new properties can be added, so the schema is intentionally not fixed.

# Setup

Start neo4j via 
```bash
docker run \
    --name testneo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

Importing the db from the hardcoded .cypher file is done automatically on startup and test start.

# Tests

```
Launching pytest with arguments -s test.py --no-header --no-summary -q in /home/m/IdeaProjects/fastapi-neo4j

============================= test session starts ==============================
collecting ... collected 10 items

test.py::test_types_nodes PASSED
test.py::test_types_relationships PASSED
test.py::test_all PASSED
test.py::test_all_students PASSED
test.py::test_all_invalid_type PASSED
test.py::test_lecture_to_student PASSED
test.py::test_has_grade PASSED
test.py::test_create_delete_node PASSED
test.py::test_create_delete_relationship PASSED
test.py::test_delete_invalid PASSED

======================= 10 passed, 153 warnings in 0.21s =======================
/usr/lib/python3.10/site-packages/neo4j/_sync/driver.py:414: DeprecationWarning: Relying on Driver's destructor to close the session is deprecated. Please make sure to close the session. Use it as a context (`with` statement) or make sure to call `.close()` explicitly. Future versions of the driver will not close drivers automatically.

Process finished with exit code 0
```
