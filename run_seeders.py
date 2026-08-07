"""Seed recipes into an already-migrated database.

Usage:
  python run_seeders.py
  # or:
  flask --app run:app seed
"""

from app import create_app
from app.seeders import seed_recipes

app = create_app()

with app.app_context():
    seed_recipes()
    print("Database seeded successfully.")
