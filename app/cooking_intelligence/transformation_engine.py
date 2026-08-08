class TransformationEngine:
    @staticmethod
    def describe(stage, ingredient_names):
        names = " ".join(ingredient_names).casefold()
        if "onion" in names:
            return {
                "before": "Raw, firm onion with a sharp aroma",
                "process": "Heat softens the cells, drives off moisture and can promote browning",
                "after": "Softer, sweeter onion with colour and aromatic depth",
                "science": (
                    "Moisture first evaporates; with enough controlled heat, browning reactions "
                    "create new aromas and colour."
                ),
            }
        if any(word in names for word in ("chicken", "fish", "egg")):
            return {
                "before": "Raw, soft protein",
                "process": "Heat changes protein structure and drives gradual firming",
                "after": "Opaque, firmer cooked protein",
                "science": (
                    "Proteins unfold and set as they heat. Use a thermometer for safety-critical "
                    "doneness rather than colour alone."
                ),
            }
        if any(word in names for word in ("rice", "lentil")):
            return {
                "before": "Dry, firm grains",
                "process": "Heat and moisture move into the grain; starch absorbs water",
                "after": "Hydrated, tender grains",
                "science": (
                    "Starch gelatinization and water absorption create the cooked texture."
                ),
            }
        if stage in {"saute", "fry", "stir_fry"}:
            return {
                "before": "Raw ingredients with surface moisture",
                "process": "Direct heat reduces moisture and develops surface colour",
                "after": "Cooked ingredients with a more developed aroma and texture",
                "science": (
                    "Heat transfer and moisture loss change texture; controlled browning can add "
                    "colour and aroma."
                ),
            }
        if stage in {"simmer", "boil", "dum"}:
            return {
                "before": "Separate ingredients and cooking liquid",
                "process": "Gentle heat transfers through the liquid and softens ingredients",
                "after": "Tender ingredients and a more cohesive cooking liquid",
                "science": (
                    "Moist heat moves energy evenly while ingredients hydrate and flavours disperse."
                ),
            }
        return {
            "before": "Ingredients before this action",
            "process": "The stored cooking action changes temperature, moisture or structure",
            "after": "Ingredients prepared for the next stage",
            "science": "Cooking changes food through heat transfer, mixing and moisture movement.",
        }
