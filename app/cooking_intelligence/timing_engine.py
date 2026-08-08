import re


class TimingEngine:
    DEFAULTS = {
        "prepare": (3, 8),
        "marinate": (20, 30),
        "preheat": (1, 3),
        "saute": (4, 8),
        "fry": (3, 7),
        "stir_fry": (3, 6),
        "boil": (8, 15),
        "simmer": (12, 25),
        "dum": (15, 25),
        "bake": (20, 40),
        "steam": (8, 15),
        "combine": (2, 5),
        "rest": (5, 10),
        "finish": (1, 2),
        "cook": (4, 10),
    }

    @classmethod
    def estimate(cls, instruction, stage):
        match = re.search(
            r"(\d+)\s*(?:-|to)?\s*(\d+)?\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)",
            instruction.casefold(),
        )
        if match:
            minimum = int(match.group(1))
            maximum = int(match.group(2) or minimum)
            unit = match.group(3)
            if unit.startswith(("second", "sec")):
                minimum = max(1, round(minimum / 60))
                maximum = max(1, round(maximum / 60))
            elif unit.startswith(("hour", "hr")):
                minimum *= 60
                maximum *= 60
            return {
                "minimum_minutes": minimum,
                "maximum_minutes": maximum,
                "estimated_minutes": round((minimum + maximum) / 2),
                "source": "stored-instruction",
            }

        minimum, maximum = cls.DEFAULTS.get(stage, cls.DEFAULTS["cook"])
        return {
            "minimum_minutes": minimum,
            "maximum_minutes": maximum,
            "estimated_minutes": round((minimum + maximum) / 2),
            "source": "contextual-estimate",
        }

    @staticmethod
    def timeline(steps):
        elapsed = 0
        for step in steps:
            duration = step["timing"]["estimated_minutes"]
            step["timeline"] = {
                "start_minute": elapsed,
                "end_minute": elapsed + duration,
            }
            elapsed += duration
        return elapsed
