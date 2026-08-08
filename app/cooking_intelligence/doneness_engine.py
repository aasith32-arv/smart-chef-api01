class DonenessEngine:
    """Observable doneness cues that complement, rather than replace, timing."""

    @classmethod
    def cues(cls, stage, instruction, ingredient_names):
        text = f"{instruction} {' '.join(ingredient_names)}".casefold()
        if "onion" in text:
            return {
                "visual_cue": "Edges soften; continue to translucent or golden as instructed.",
                "colour_stage": "softening → translucent → golden → deep brown/burn risk",
                "colour_progress": 70 if "gold" in text or "brown" in text else 50,
                "texture_cue": "Soft and pliable, not crisp or charred.",
                "aroma_cue": "Sharp raw aroma becomes sweeter; acrid smoke means burning.",
            }
        if any(word in text for word in ("chicken", "fish", "egg")):
            return {
                "visual_cue": "The exterior becomes opaque and firm; verify internal temperature.",
                "colour_stage": "raw → opaque exterior → cooked interior",
                "colour_progress": 65,
                "texture_cue": "Firm and cooked, but not dry or rubbery.",
                "aroma_cue": "Raw aroma disappears; there should be no scorched smell.",
            }
        if any(word in text for word in ("rice", "lentil")):
            return {
                "visual_cue": "Grains look hydrated; check a grain rather than relying only on time.",
                "colour_stage": "dry/opaque → hydrated and cooked",
                "colour_progress": 70,
                "texture_cue": "Tender at the centre; separate or creamy according to the recipe.",
                "aroma_cue": "A clean cooked-grain aroma replaces the raw starchy smell.",
            }
        if stage in {"saute", "fry", "stir_fry"}:
            return {
                "visual_cue": "Surfaces should cook evenly with no black or smoking patches.",
                "colour_stage": "raw → lightly coloured → browned → burn risk",
                "colour_progress": 60,
                "texture_cue": "Tenderness develops while the intended structure remains.",
                "aroma_cue": "A cooked, fragrant aroma should develop without acrid smoke.",
            }
        if stage in {"simmer", "boil", "dum"}:
            return {
                "visual_cue": "Look for the bubble level and consistency described in the step.",
                "colour_stage": "mixed → cohesive, cooked appearance",
                "colour_progress": 70,
                "texture_cue": "Check the largest or densest piece for tenderness.",
                "aroma_cue": "Raw aromas should soften into a balanced cooked aroma.",
            }
        return {
            "visual_cue": "Look for the observable change described in the instruction.",
            "colour_stage": "Visual estimate varies with lighting and cookware.",
            "colour_progress": 40,
            "texture_cue": "Check texture directly; time is only an estimate.",
            "aroma_cue": "Expect a clean cooked aroma, never an acrid or scorched smell.",
        }
