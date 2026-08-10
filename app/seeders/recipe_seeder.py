import json
import os
from pathlib import Path

from app.extensions import db
from app.models import DishFamily, Ingredient, Recipe
from app.seeders.catalog_biryani import biryani_catalog
from app.seeders.catalog_classics import classics_catalog
from app.seeders.catalog_curries import curry_catalog
from app.seeders.catalog_sides import sides_catalog
from app.seeders.catalog_staples import staple_catalog
from app.utils import slugify

RECIPE_METADATA_FIELDS = (
    "cuisine",
    "region",
    "protein",
    "diet_type",
    "difficulty",
    "prep_time",
    "cook_time",
    "spice_level",
    "tags",
)


def _data_dir():
    return Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data")))


def _read_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_recipe_catalog(data_dir):
    catalog = []
    legacy_path = data_dir / "recipes.json"
    if legacy_path.exists():
        catalog.extend(_read_json(legacy_path))

    catalog_dir = data_dir / "recipe_catalog"
    if catalog_dir.exists():
        for path in sorted(catalog_dir.glob("*.json")):
            catalog.extend(_read_json(path))
    catalog.extend(biryani_catalog())
    catalog.extend(curry_catalog())
    catalog.extend(staple_catalog())
    catalog.extend(classics_catalog())
    catalog.extend(sides_catalog())
    return catalog


def _seed_families(data_dir):
    path = data_dir / "dish_families.json"
    if not path.exists():
        return {}, 0, 0

    created = 0
    updated = 0
    by_slug = {}
    for item in _read_json(path):
        slug = item.get("slug") or slugify(item["name"])
        family = DishFamily.query.filter(DishFamily.slug.ilike(slug)).first()
        if family is None:
            family = DishFamily(slug=slug)
            db.session.add(family)
            created += 1
        elif family.managed_by_admin:
            by_slug[slug] = family
            continue
        else:
            updated += 1
        for field in ("name", "description", "category", "image", "is_active"):
            if field in item:
                setattr(family, field, item[field])
        by_slug[slug] = family
    db.session.flush()
    return by_slug, created, updated


def _new_recipe(item, family):
    recipe = Recipe(
        name=item["name"],
        slug=item.get("slug") or slugify(item["name"]),
        category=item["category"],
        family=family,
        description=item.get("description", ""),
        serving_size=item["serving_size"],
        steps=item["steps"],
        image=item.get("image") or "",
    )
    for field in RECIPE_METADATA_FIELDS:
        if field in item:
            setattr(recipe, field, item[field])
    for ingredient in item["ingredients"]:
        recipe.ingredients.append(
            Ingredient(
                name=ingredient["name"].strip(),
                quantity=ingredient["quantity"],
                unit=ingredient["unit"].strip(),
            )
        )
    return recipe


def _enrich_existing_recipe(recipe, item, family):
    """Add discovery metadata without replacing existing recipe content or IDs."""
    if recipe.managed_by_admin:
        return False
    changed = False
    values = {
        "slug": item.get("slug") or slugify(item["name"]),
        "family": family,
        **{field: item.get(field) for field in RECIPE_METADATA_FIELDS},
    }
    for field, value in values.items():
        current = getattr(recipe, field)
        if value is not None and (current is None or current == ""):
            setattr(recipe, field, value)
            changed = True
    return changed


def seed_recipes():
    """Idempotently add families and curated recipes to an already-migrated DB."""
    data_dir = _data_dir()
    families, families_created, families_updated = _seed_families(data_dir)
    catalog = _load_recipe_catalog(data_dir)

    created = 0
    enriched = 0
    skipped = 0
    seen_slugs = set()
    seen_names = set()

    for item in catalog:
        slug = item.get("slug") or slugify(item["name"])
        normalized_name = item["name"].strip().casefold()
        if slug in seen_slugs or normalized_name in seen_names:
            raise ValueError(f"Duplicate recipe seed entry: {item['name']}")
        seen_slugs.add(slug)
        seen_names.add(normalized_name)

        family_slug = item.get("family_slug")
        family = families.get(family_slug) if family_slug else None
        if family_slug and family is None:
            raise ValueError(
                f"Recipe '{item['name']}' references unknown family '{family_slug}'."
            )

        existing = Recipe.query.filter(Recipe.slug.ilike(slug)).first()
        if existing is None:
            existing = Recipe.query.filter(Recipe.name.ilike(item["name"].strip())).first()
        if existing is not None:
            if _enrich_existing_recipe(existing, item, family):
                enriched += 1
            else:
                skipped += 1
            continue

        db.session.add(_new_recipe(item, family))
        created += 1

    db.session.commit()
    result = {
        "families_created": families_created,
        "families_updated": families_updated,
        "recipes_created": created,
        "recipes_enriched": enriched,
        "recipes_skipped": skipped,
    }
    print(
        "Catalog seeding complete: "
        f"{families_created} families created, {families_updated} families updated, "
        f"{created} recipes created, {enriched} recipes enriched, {skipped} recipes unchanged."
    )
    return result
