from unittest.mock import patch

from app.ai.cooking_explanation_service import CookingExplanationService
from app.cooking_intelligence.cooking_plan_service import CookingPlanService
from app.cooking_intelligence.cooking_validation_service import CookingValidationService
from app.services.ai_service import AIService


def test_plan_scales_quantities_and_builds_recipe_specific_sequence(sample_recipe):
    sample_recipe.steps = [
        "Heat oil over medium heat.",
        "Saute onion until golden, 5-7 minutes.",
        "Add chicken and simmer for 20 minutes.",
    ]

    plan, errors = CookingPlanService.build(sample_recipe, {"servings": 8})

    assert errors is None
    assert plan["servings"] == 8
    assert plan["source"] == "rule-based"
    chicken = next(item for item in plan["ingredients"] if item["name"] == "Chicken")
    assert chicken["quantity"] == 1000
    assert chicken["display"] == "1 kg"
    assert [step["stage"] for step in plan["steps"]] == [
        "preheat",
        "saute",
        "simmer",
    ]
    assert plan["steps"][1]["ingredients"][0]["name"] == "Onion"
    assert "why_now" in plan["steps"][1]["ingredients"][0]


def test_temperature_and_sequence_validation(sample_recipe):
    sample_recipe.steps = ["Saute onion until soft for 4 minutes."]
    plan, errors = CookingPlanService.build(sample_recipe)

    assert errors is None
    temperature = plan["steps"][0]["temperature"]
    assert temperature["minimum_c"] == 140
    assert temperature["maximum_c"] == 175
    assert CookingValidationService.validate_plan(plan, sample_recipe) == []

    plan["steps"][0]["temperature"]["minimum_c"] = 220
    plan["steps"][0]["temperature"]["maximum_c"] = 120
    assert "minimum temperature exceeds maximum" in " ".join(
        CookingValidationService.validate_plan(plan, sample_recipe)
    )


def test_invalid_recipe_without_steps_fails_validation(sample_recipe):
    sample_recipe.steps = []

    plan, errors = CookingPlanService.build(sample_recipe)

    assert plan is None
    assert "Cooking plan requires at least one step." in errors["plan"]


def test_personalization_adjusts_spice_oil_and_salt(sample_recipe):
    sample_recipe.ingredients[0].name = "Chili Powder"
    sample_recipe.ingredients[1].name = "Salt"
    sample_recipe.ingredients[2].name = "Oil"
    sample_recipe.steps = ["Add chili powder, salt and oil, then stir."]

    plan, errors = CookingPlanService.build(
        sample_recipe,
        {
            "servings": 4,
            "spice_level": "mild",
            "salt_preference": "low",
            "oil_level": "low",
        },
    )

    assert errors is None
    quantities = {item["name"]: item["quantity"] for item in plan["ingredients"]}
    assert quantities == {"Chili Powder": 350, "Salt": 1.5, "Oil": 22.5}


def test_malformed_ai_explanation_uses_validated_fallback():
    with (
        patch.object(AIService, "is_configured", return_value=True),
        patch.object(AIService, "_chat", return_value={"unexpected": "shape"}),
    ):
        result = CookingExplanationService.explain("add onion", use_ai=True)

    assert result["source"] == "rule-based-fallback"
    assert result["explanation"]
