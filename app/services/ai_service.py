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
