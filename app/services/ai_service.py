"""OpenAI-backed meal planning with local recipe fallbacks."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request


class AIService:
    """Generate meal plans, suggestions, and translations via OpenAI when configured."""

    DEFAULT_MODEL = "gpt-4o-mini"
    OPENAI_URL = "https://api.openai.com/v1/chat/completions"

    @classmethod
    def api_key(cls):
        return (os.getenv("OPENAI_API_KEY") or "").strip()

    @classmethod
    def model(cls):
        return (os.getenv("OPENAI_MODEL") or cls.DEFAULT_MODEL).strip()

    @classmethod
    def is_configured(cls):
        key = cls.api_key()
        return bool(key) and key.startswith("sk-") and "your-real-key" not in key

    @classmethod
    def status(cls):
        configured = cls.is_configured()
        model = cls.model()
        if configured:
            message = f"OpenAI ready ({model}). AI plans and suggestions are available."
        else:
            message = (
                "OpenAI key missing. Local recipes still work. "
                "Set OPENAI_API_KEY in smart-chef-api/.env for AI plans."
            )
        return {
            "configured": configured,
            "model": model,
            "message": message,
            "reachable": True,
        }

    @classmethod
    def _chat(cls, system_prompt, user_prompt, temperature=0.4):
        if not cls.is_configured():
            raise RuntimeError("OpenAI is not configured.")

        payload = {
            "model": cls.model(),
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        request = urllib.request.Request(
            cls.OPENAI_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cls.api_key()}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI request failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI unreachable: {exc.reason}") from exc

        content = body["choices"][0]["message"]["content"]
        return json.loads(content)

    @staticmethod
    def _parse_display(display, unit_hint=""):
        text = (display or "").strip()
        match = re.match(r"^([\d.]+)\s*(.*)$", text)
        if not match:
            return 0.0, unit_hint or ""
        quantity = float(match.group(1))
        unit = (match.group(2) or unit_hint or "").strip()
        return quantity, unit

    @classmethod
    def meal_plan_from_recipe(cls, recipe, people, language="en"):
        """Build an AIMealPlan-shaped payload from a local recipe (no OpenAI)."""
        from app.services.calculator_service import QuantityCalculatorService

        quantities, error = QuantityCalculatorService.calculate_for_recipe(recipe, people)
        if error:
            raise ValueError(error)

        ingredients = []
        scale = people / max(recipe.serving_size, 1)
        for ingredient in recipe.ingredients:
            display = quantities.get(ingredient.name) or QuantityCalculatorService.format_quantity(
                ingredient.quantity * scale, ingredient.unit
            )
            quantity, unit = cls._parse_display(display, ingredient.unit)
            ingredients.append(
                {
                    "name": ingredient.name,
                    "quantity": quantity,
                    "unit": unit or ingredient.unit,
                    "display": display,
                }
            )

        return {
            "dish": recipe.name,
            "category": recipe.category,
            "description": recipe.description or f"Scaled for {people} people from the recipe library.",
            "people": people,
            "ingredients": ingredients,
            "steps": recipe.steps or [],
            "tips": [
                f"Base recipe serves {recipe.serving_size}; quantities scaled to {people} people."
            ],
            "source": "local",
            "language": language or "en",
        }

    @classmethod
    def generate_meal_plan(cls, dish, people, language="en"):
        system = (
            "You are AI Chef, a professional kitchen planner. "
            "Return ONLY valid JSON with keys: dish, category, description, people, "
            "ingredients (array of {name, quantity, unit, display}), steps (string array), "
            "tips (string array), source, language. "
            "Quantities must be realistic for the given guest count. "
            "Write all text fields in the requested language code."
        )
        user = json.dumps(
            {
                "dish": dish,
                "people": people,
                "language": language,
                "source": "openai",
            }
        )
        data = cls._chat(system, user)
        data["people"] = people
        data["source"] = data.get("source") or "openai"
        data["language"] = language
        data.setdefault("dish", dish)
        data.setdefault("category", "General")
        data.setdefault("description", "")
        data.setdefault("ingredients", [])
        data.setdefault("steps", [])
        data.setdefault("tips", [])

        for item in data["ingredients"]:
            if not item.get("display"):
                qty = item.get("quantity", 0)
                unit = item.get("unit", "")
                item["display"] = f"{qty} {unit}".strip()
            if "quantity" not in item:
                qty, unit = cls._parse_display(item.get("display", ""))
                item["quantity"] = qty
                item.setdefault("unit", unit)
        return data

    @classmethod
    def suggest_from_local(cls, recommendations, available_ingredients):
        suggestions = []
        for item in recommendations:
            recipe = item["recipe"]
            suggestions.append(
                {
                    "name": recipe["name"],
                    "category": recipe.get("category") or "General",
                    "match_percentage": item.get("match_percentage", 0),
                    "description": recipe.get("description") or "",
                    "missing_ingredients": item.get("missing_ingredients") or [],
                    "why": (
                        f"{item.get('match_percentage', 0)}% ingredient match "
                        "from your pantry."
                    ),
                }
            )
        return {
            "available_ingredients": available_ingredients,
            "count": len(suggestions),
            "suggestions": suggestions,
            "source": "local",
        }

    @classmethod
    def generate_suggestions(cls, ingredients, language="en"):
        system = (
            "You are AI Chef. Suggest dishes that can be made from the pantry list. "
            "Return ONLY valid JSON with keys: available_ingredients, count, suggestions "
            "(array of {name, category, match_percentage, description, missing_ingredients, why}), "
            "source. Write text in the requested language. Prefer realistic home cooking."
        )
        user = json.dumps({"ingredients": ingredients, "language": language, "source": "openai"})
        data = cls._chat(system, user, temperature=0.5)
        data["available_ingredients"] = ingredients
        data["source"] = data.get("source") or "openai"
        suggestions = data.get("suggestions") or []
        data["suggestions"] = suggestions
        data["count"] = len(suggestions)
        return data

    @classmethod
    def translate_content(cls, content, language):
        if language in (None, "", "en"):
            return {
                "dish": content.get("dish") or content.get("name") or "",
                "description": content.get("description") or "",
                "ingredients": content.get("ingredients") or [],
                "steps": content.get("steps") or [],
                "tips": content.get("tips") or [],
                "language": "en",
                "source": "passthrough",
            }

        if not cls.is_configured():
            return {
                "dish": content.get("dish") or content.get("name") or "",
                "description": content.get("description") or "",
                "ingredients": content.get("ingredients") or [],
                "steps": content.get("steps") or [],
                "tips": content.get("tips") or [],
                "language": language,
                "source": "local-passthrough",
            }

        system = (
            "Translate the recipe content into the target language. "
            "Keep ingredient quantities and units unchanged in display strings unless "
            "the unit name must be localized. Return ONLY JSON with keys: dish, description, "
            "ingredients (same shape as input), steps, tips, language, source."
        )
        user = json.dumps({"content": content, "language": language, "source": "openai"})
        data = cls._chat(system, user, temperature=0.2)
        data["language"] = language
        data["source"] = data.get("source") or "openai"
        data.setdefault("dish", content.get("dish") or "")
        data.setdefault("description", content.get("description") or "")
        data.setdefault("ingredients", content.get("ingredients") or [])
        data.setdefault("steps", content.get("steps") or [])
        data.setdefault("tips", content.get("tips") or [])
        return data
