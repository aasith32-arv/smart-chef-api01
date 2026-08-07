def test_ai_status_route(client):
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert "configured" in body["data"]


def test_ai_plan_route(client, sample_recipe):
    res = client.post(
        "/api/v1/ai/plan",
        json={"dish": sample_recipe.name, "people": 4},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["dish"] == sample_recipe.name


def test_ai_routes_not_at_api_root(client):
    """Blueprint /ai prefix must survive /api/v1 registration."""
    assert client.get("/api/v1/status").status_code == 404
    assert client.get("/api/v1/ai/status").status_code == 200
