import re


class CookingSequenceEngine:
    """Derive recipe-specific stages and ingredient additions from stored instructions."""

    STAGE_KEYWORDS = (
        ("marinate", ("marinate", "marination")),
        ("prepare", ("wash", "rinse", "soak", "chop", "slice", "dice", "clean")),
        ("preheat", ("preheat", "heat oil", "heat a", "heat the")),
        ("dum", ("dum", "cover tightly")),
        ("boil", ("boil", "parboil")),
        ("simmer", ("simmer", "gentle bubbles")),
        ("stir_fry", ("stir-fry", "stir fry", "toss on high", "wok")),
        ("fry", ("fry", "scramble")),
        ("saute", ("sauté", "saute", "soften", "brown")),
        ("bake", ("bake", "roast", "oven")),
        ("steam", ("steam",)),
        ("combine", ("add", "mix", "stir", "pour", "layer")),
        ("rest", ("rest", "cool", "set aside")),
        ("finish", ("garnish", "serve", "adjust seasoning")),
    )

    INGREDIENT_GROUPS = {
        "vegetable": (
            "carrot",
            "beans",
            "capsicum",
            "potato",
            "leeks",
            "vegetable",
        ),
        "spice": (
            "powder",
            "masala",
            "turmeric",
            "pepper",
            "mustard",
            "spice",
            "chili",
            "chilli",
        ),
        "herb": ("mint", "coriander", "curry leaves", "spring onion"),
        "protein": ("chicken", "fish", "egg", "beef", "pork", "lamb"),
        "liquid": ("water", "stock", "coconut milk"),
        "seasoning": ("salt", "soy sauce", "pepper"),
    }

    @classmethod
    def classify_stage(cls, instruction):
        text = instruction.casefold().strip()
        if re.match(r"^(wash|rinse|soak|chop|slice|dice|clean)\b", text):
            return "prepare"
        if re.match(r"^(marinate|marination)\b", text):
            return "marinate"
        for stage, keywords in cls.STAGE_KEYWORDS:
            if stage in {"prepare", "marinate"}:
                continue
            if any(re.search(rf"\b{re.escape(keyword)}\b", text) for keyword in keywords):
                return stage
        return "cook"

    @staticmethod
    def title_for(instruction, stage):
        clean = re.sub(r"\s+", " ", instruction).strip().rstrip(".")
        if len(clean) <= 58:
            return clean
        labels = {
            "marinate": "Marinate the ingredients",
            "prepare": "Prepare the ingredients",
            "preheat": "Heat the cooking vessel",
            "boil": "Boil until ready",
            "simmer": "Simmer gently",
            "stir_fry": "Stir-fry the ingredients",
            "fry": "Fry with controlled heat",
            "saute": "Build the flavour base",
            "combine": "Combine the ingredients",
            "dum": "Finish on low heat",
            "rest": "Rest before continuing",
            "finish": "Finish and serve",
            "cook": "Continue cooking",
        }
        return labels.get(stage, "Continue cooking")

    @classmethod
    def ingredients_for_step(cls, instruction, ingredients):
        text = instruction.casefold().replace("-", " ")
        matched = []
        for ingredient in ingredients:
            name = ingredient.name.casefold().replace("-", " ")
            tokens = [token for token in re.split(r"\W+", name) if len(token) > 2]
            if name in text or (tokens and all(token in text for token in tokens)):
                matched.append(ingredient)

        for group, keywords in cls.INGREDIENT_GROUPS.items():
            if group not in text and not any(word in text for word in keywords):
                continue
            for ingredient in ingredients:
                name = ingredient.name.casefold()
                if ingredient not in matched and any(word in name for word in keywords):
                    matched.append(ingredient)
        return matched

    @classmethod
    def ingredient_guidance(cls, ingredient, stage):
        name = ingredient.name.casefold()
        kind = cls._ingredient_kind(name)
        guidance = {
            "fat": {
                "why": "It creates an even cooking medium for the ingredients that follow.",
                "contribution": "heat transfer, richness and flavour distribution",
                "early": "Adding it before the pan is ready can make heating less predictable.",
                "late": "Later additions may not cook or coat evenly.",
                "change": "Cool fat becomes fluid and ready to carry flavour.",
            },
            "onion": {
                "why": "Onion needs time to soften and build the recipe's aromatic base.",
                "contribution": "sweetness, body, colour and aroma",
                "early": "Very high heat at the start can burn the edges before the centre softens.",
                "late": "It may remain sharp and undercooked in the finished dish.",
                "change": "Raw and firm → softened → translucent or browned as directed.",
            },
            "aromatic": {
                "why": "A short controlled cook reduces raw harshness without scorching it.",
                "contribution": "aroma and savoury depth",
                "early": "Long exposure to hot oil can make delicate aromatics bitter.",
                "late": "The raw aroma may remain dominant.",
                "change": "Raw, sharp aroma → rounded cooked aroma.",
            },
            "spice": {
                "why": "This stage lets the seasoning disperse without prolonged dry heat.",
                "contribution": "colour, aroma and flavour complexity",
                "early": "Dry spices can scorch in very hot fat.",
                "late": "They may taste dusty or remain unevenly distributed.",
                "change": "Dry spice aroma → warm, integrated aroma.",
            },
            "protein": {
                "why": "It now has contact with the developed flavour base and controlled heat.",
                "contribution": "structure, savoury flavour and substance",
                "early": "It can release moisture before the flavour base is ready.",
                "late": "It may not have enough time to cook safely and evenly.",
                "change": "Raw protein → firmer, opaque cooked structure.",
            },
            "grain": {
                "why": "The liquid and flavour base are ready for even absorption.",
                "contribution": "body and the main texture of the dish",
                "early": "Uneven liquid or heat can cause patchy cooking.",
                "late": "It may remain hard while the other ingredients overcook.",
                "change": "Dry, firm grain → hydrated and tender grain.",
            },
            "vegetable": {
                "why": "This timing balances tenderness with the intended texture.",
                "contribution": "colour, texture, moisture and flavour",
                "early": "Delicate vegetables may become overly soft.",
                "late": "Dense vegetables may remain firm or raw.",
                "change": "Raw and firm → brighter or softened as the recipe requires.",
            },
            "liquid": {
                "why": "The flavour base is ready to be loosened and cooked evenly.",
                "contribution": "moisture, sauce consistency and heat distribution",
                "early": "Browning and flavour development may be reduced.",
                "late": "The dish may cook dry or the liquid may not integrate.",
                "change": "Separate liquid and solids → a unified sauce or cooking medium.",
            },
            "herb": {
                "why": "Adding delicate herbs late preserves more of their fresh character.",
                "contribution": "fresh aroma, colour and finishing flavour",
                "early": "Their fresh aroma and colour can fade during long cooking.",
                "late": "They may not distribute through the dish.",
                "change": "Fresh herb → gently wilted, aromatic finish.",
            },
            "seasoning": {
                "why": "Seasoning here allows it to distribute and still be adjusted later.",
                "contribution": "balance and overall flavour definition",
                "early": "Reduction can concentrate seasoning more than expected.",
                "late": "It may not dissolve or spread evenly.",
                "change": "Separate seasoning → evenly distributed flavour.",
            },
            "other": {
                "why": f"This stage follows the stored method for {ingredient.name}.",
                "contribution": "the recipe's intended flavour and texture",
                "early": "The ingredient may interfere with an earlier cooking stage.",
                "late": "It may not have enough time to integrate.",
                "change": "The ingredient cooks and combines with the surrounding mixture.",
            },
        }[kind]
        return {
            "why_now": guidance["why"],
            "contribution": guidance["contribution"],
            "added_too_early": guidance["early"],
            "added_too_late": guidance["late"],
            "expected_transformation": guidance["change"],
            "visual_cue": cls._ingredient_visual(kind, stage),
            "aroma_cue": cls._ingredient_aroma(kind),
            "texture_cue": cls._ingredient_texture(kind),
        }

    @staticmethod
    def _ingredient_kind(name):
        if any(word in name for word in ("oil", "ghee", "butter")):
            return "fat"
        if "onion" in name or "shallot" in name:
            return "onion"
        if any(word in name for word in ("garlic", "ginger")):
            return "aromatic"
        if any(
            word in name
            for word in ("powder", "masala", "turmeric", "mustard", "chili", "pepper")
        ):
            return "spice"
        if any(word in name for word in ("chicken", "fish", "egg", "beef", "pork", "lamb")):
            return "protein"
        if any(word in name for word in ("rice", "lentil", "roti", "flour")):
            return "grain"
        if any(word in name for word in ("milk", "water", "stock", "sauce", "yogurt")):
            return "liquid"
        if any(word in name for word in ("mint", "coriander", "leaves", "spring onion")):
            return "herb"
        if "salt" in name:
            return "seasoning"
        if any(
            word in name
            for word in ("carrot", "bean", "capsicum", "potato", "tomato", "leek")
        ):
            return "vegetable"
        return "other"

    @staticmethod
    def _ingredient_visual(kind, stage):
        cues = {
            "onion": "Look for softened edges and the colour named in the instruction.",
            "protein": "Look for an opaque exterior; use a thermometer for safe doneness.",
            "grain": "Grains should look hydrated and separate or tender as directed.",
            "vegetable": "Look for a brighter colour and the intended tenderness.",
            "spice": "Spices should moisten into the mixture without dark burnt patches.",
            "aromatic": "The paste should lose its wet raw appearance without browning too far.",
        }
        return cues.get(kind, "Look for even mixing and the change described in the instruction.")

    @staticmethod
    def _ingredient_aroma(kind):
        return {
            "onion": "The sharp raw-onion smell becomes sweeter and rounder.",
            "aromatic": "The sharp raw aroma reduces and becomes fragrant.",
            "spice": "A warm spice aroma should emerge; smoke signals excessive heat.",
            "protein": "The raw aroma should disappear as it cooks.",
            "herb": "A fresh herbal aroma should remain noticeable.",
        }.get(kind, "The aroma should smell cooked and balanced, never scorched.")

    @staticmethod
    def _ingredient_texture(kind):
        return {
            "onion": "Firm slices soften and become pliable.",
            "protein": "The exterior firms as the protein cooks.",
            "grain": "Hard grains absorb moisture and become tender.",
            "vegetable": "Raw firmness reduces while some structure remains.",
            "liquid": "The liquid becomes integrated with the solids.",
        }.get(kind, "The ingredient should integrate without burning or becoming mushy.")
