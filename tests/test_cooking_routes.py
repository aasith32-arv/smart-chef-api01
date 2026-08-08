def test_get_cooking_plan_with_scaled_servings(client, sample_recipe):
    sample_recipe.steps = [
        "Heat oil.",
        "Saute onion for 5 minutes.",
        "Add chicken and simmer for 20 minutes.",
    ]

    response = client.get(
        f"/api/v1/recipes/{sample_recipe.id}/cooking-plan?servings=8"
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["servings"] == 8
    assert len(body["data"]["steps"]) == 3


def test_personalized_cooking_plan_rejects_invalid_preferences(client, sample_recipe):
    response = client.post(
        f"/api/v1/recipes/{sample_recipe.id}/cooking-plan",
        json={"servings": 0, "spice_level": "extreme"},
    )

    assert response.status_code == 400
    assert "servings" in response.get_json()["errors"]


def test_cooking_plan_missing_recipe(client):
    response = client.get("/api/v1/recipes/999999/cooking-plan")

    assert response.status_code == 404


def test_troubleshooting_route(client):
    response = client.post(
        "/api/v1/cooking/troubleshoot", json={"problem": "too watery"}
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["probable_cause"]
    assert result["immediate_action"]
    assert result["recovery_option"]
    assert result["prevention_tip"]


def test_substitution_route_is_contextual(client, sample_recipe):
    response = client.post(
        "/api/v1/cooking/substitute",
        json={"ingredient": "yogurt", "recipe_id": sample_recipe.id},
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["options"][0]["how_much"]
    assert result["options"][0]["what_changes"]


def test_recipe_mutation_still_requires_authentication(client):
    response = client.post("/api/v1/recipes", json={})

    assert response.status_code == 401
