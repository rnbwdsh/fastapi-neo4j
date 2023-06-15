import pytest
from main import app, ELEMENT_ID
from fastapi.testclient import TestClient
client = TestClient(app)


def test_all():
    response = client.get("/data")
    assert response.status_code == 200
    assert len(response.json()) == 40


def test_all_students():
    response = client.get("/data/Student")
    assert response.status_code == 200
    assert len(response.json()) == 8
    names = set([node["name"] for node in response.json()])
    assert names == {'Han', 'Robin', 'Marian', 'Elvin', 'Alex', 'Luca', 'Sam', 'Kim'}


def test_all_invalid_type():
    response = client.get("/data/InvalidType")
    assert response.status_code == 422


def test_lecture_to_student():
    response = client.get("/data/Lecture/Student")
    assert response.status_code == 200
    assert all(r["type"] in ["HEARS", "HAS_GRADE"] for r in response.json())


def test_has_grade():
    response = client.get("/data/Student/Exam")
    assert response.status_code == 200
    assert all(r["type"] == "REGISTERS" or
               r["type"] == "HAS_GRADE" and r["properties"]
               for r in response.json())

    # check for one simple entry
    exam = {'date': '2023-04-18', 'note': 'Second exam', 'room': 'HS 1'}
    entry = next(r for r in response.json()
                 if r["source"]["name"] == "Han" and
                 r["type"] == "HAS_GRADE" and
                 r["target"] == exam)
    assert entry["properties"]["grade"] == 2


def test_create_delete_node():
    response = client.post("/node/Student", json={"name": "Daniel"})
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Daniel"
    node_id = response.json()[0][ELEMENT_ID]

    response = client.delete(f"/node/{node_id}")
    assert response.status_code == 200
    assert response.json() == {"message": "Node deleted."}


def test_create_delete_relationship():
    """ Student Alex hears Lecture Betriebssysteme """
    students = client.get("/data/Student").json()
    alex_id = next(s[ELEMENT_ID] for s in students if s["name"] == "Alex")
    lectures = client.get("/data/Lecture").json()
    bs_id = next(s[ELEMENT_ID] for s in lectures if s["topic"] == "Betriebssysteme")

    response = client.post(f"/relationship/{alex_id}/HEARS/{bs_id}", json={})
    assert response.status_code == 200
    rel_id = response.json()[0][ELEMENT_ID]

    response = client.delete(f"/relationship/{rel_id}")
    assert response.status_code == 200


def test_delete_invalid_node():
    response = client.delete(f"/node/9999999999999999")
    assert response.status_code == 400


def test_delete_invalid_rel():
    response = client.delete(f"/relationship/9999999999999999")
    assert response.status_code == 400


def test_edit_student():
    first_student_id = client.get("/data/Student").json()[0][ELEMENT_ID]
    response = client.post(f"/edit/node/{first_student_id}", json={"name": "Daniel"})
    assert response.status_code == 200
