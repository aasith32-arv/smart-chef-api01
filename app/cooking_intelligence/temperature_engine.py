class TemperatureEngine:
    """Contextual heat guidance; ranges describe cooking conditions, not guarantees."""

    GUIDES = {
        "preheat": ("MEDIUM", 140, 175, "Warm the vessel gradually before cooking."),
        "saute": ("MEDIUM", 140, 175, "Support softening and browning without scorching."),
        "fry": ("MEDIUM-HIGH", 160, 190, "Promote surface cooking while retaining control."),
        "stir_fry": ("HIGH", 175, 205, "Cook small pieces quickly while tossing frequently."),
        "boil": ("HIGH → MEDIUM", 95, 100, "Reach a boil, then adjust to avoid overflow."),
        "simmer": ("LOW", 85, 96, "Maintain small bubbles for gentle, even cooking."),
        "dum": ("LOW", 85, 110, "Use gentle enclosed heat to finish without scorching."),
        "bake": ("OVEN", 160, 220, "Use the recipe's oven setting and check doneness."),
        "steam": ("MEDIUM", 98, 100, "Maintain steady steam without boiling the pan dry."),
        "combine": ("LOW-MEDIUM", None, None, "Adjust heat to the surrounding cooking stage."),
        "cook": ("MEDIUM", None, None, "Adjust heat using the observable cues, not time alone."),
    }

    @classmethod
    def guidance(cls, stage, ingredient_names):
        if stage in {"prepare", "marinate", "rest", "finish"}:
            heat, low, high, reason = "OFF", None, None, "No active heat is normally needed."
            food_safety = None
        else:
            heat, low, high, reason = cls.GUIDES.get(stage, cls.GUIDES["cook"])
            food_safety = cls.food_safety_note(ingredient_names)
        return {
            "heat_level": heat,
            "minimum_c": low,
            "maximum_c": high,
            "reason": reason,
            "context": (
                "Approximate cooking-condition range. Actual pan temperature varies with "
                "cookware, stove, batch size and ingredient moisture. Follow visual and aroma cues."
            ),
            "food_safety": food_safety,
        }

    @staticmethod
    def food_safety_note(ingredient_names):
        names = " ".join(ingredient_names).casefold()
        if any(word in names for word in ("chicken", "turkey", "poultry")):
            return (
                "For safety, verify poultry reaches 74°C (165°F) internally with a food "
                "thermometer; colour and time alone do not prove doneness."
            )
        if "fish" in names:
            return (
                "For safety, verify fish reaches 63°C (145°F) internally with a food "
                "thermometer; appearance and time are supporting cues only."
            )
        return None
