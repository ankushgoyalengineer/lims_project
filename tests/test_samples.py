# tests/test_samples.py
def test_create_sample_and_list(client):
    # create a project first (owner is overridden by fixture)
    r = client.post("/projects", json={"name": "Proj for samples", "description": "pdesc"})
    assert r.status_code == 201
    project_id = r.json()["id"]

    # create sample attached to that project
    sample_payload = {
        "barcode": "TST-S001",
        "sample_type": "Blood",
        "project_id": project_id,
        "metadata": {"donor": "D100", "collection_date": "2025-10-25"}
    }
    r = client.post("/samples", json=sample_payload)
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["barcode"] == "TST-S001"
    assert s["project_id"] == project_id
    assert isinstance(s["metadata"], dict)
    assert s["metadata"]["donor"] == "D100"

    # get sample by id
    sample_id = s["id"]
    r = client.get(f"/samples/{sample_id}")
    assert r.status_code == 200
    s2 = r.json()
    assert s2["id"] == sample_id

def test_get_project_samples(client):
    # create project + two samples
    r = client.post("/projects", json={"name": "Proj samples 2", "description": "pdesc2"})
    project_id = r.json()["id"]

    client.post("/samples", json={"barcode": "TST-S002", "sample_type": "Serum", "project_id": project_id, "metadata": {}})
    client.post("/samples", json={"barcode": "TST-S003", "sample_type": "Plasma", "project_id": project_id, "metadata": {}})

    r = client.get(f"/projects/{project_id}/samples")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert len(items) >= 2
