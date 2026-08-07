import json
import os

from app.extensions import db
from app.models import Ingredient, Recipe


def seed_recipes():
    """Load sample recipes from data/recipes.json into the database."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_path = os.path.join(base_dir, "data", "recipes.json")

    if not os.path.exists(json_path):
        print(f"Recipe data file not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as file:
        recipes_data = json.load(file)

    created = 0
    skipped = 0

    for item in recipes_data:
        existing = Recipe.query.filter(Recipe.name.ilike(item["name"])).first()
        if existing:
            skipped += 1
            continue

        recipe = Recipe(
            name=item["name"],
            category=item["category"],
            description=item.get("description", ""),
            serving_size=item["serving_size"],
            steps=item["steps"],
            image=item.get("image", ""),
        )

        for ing in item["ingredients"]:
            recipe.ingredients.append(
                Ingredient(
                    name=ing["name"],
                    quantity=ing["quantity"],
                    unit=ing["unit"],
                )
            )

        db.session.add(recipe)
        created += 1

    db.session.commit()
    print(f"Recipe seeding complete: {created} created, {skipped} skipped.")
