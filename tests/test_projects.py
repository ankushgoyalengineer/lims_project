# tests/test_projects.py
def test_create_and_get_project(client):
    # create
    r = client.post("/projects", json={"name": "Proj A", "description": "desc A"})
    assert r.status_code == 201, r.text
    pj = r.json()
    assert pj["name"] == "Proj A"
    assert "id" in pj

    project_id = pj["id"]

    # get single
    r = client.get(f"/projects/{project_id}")
    assert r.status_code == 200
    got = r.json()
    assert got["id"] == project_id
    assert got["name"] == "Proj A"

def test_list_projects(client):
    r = client.get("/projects")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
