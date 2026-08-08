class TroubleshootingEngine:
    """Conservative recovery guidance for common cooking problems."""

    PROBLEMS = {
        "too salty": (
            "Seasoning was concentrated or added too quickly.",
            "Stop adding salt. Dilute with an unsalted compatible ingredient or liquid in small amounts.",
            "Balance the full dish and recheck before serving; severe over-salting may not be fully recoverable.",
            "Season gradually and taste after reduction stages.",
        ),
        "too spicy": (
            "The chilli level is high for the current volume.",
            "Add a compatible unsalted base, dairy/coconut component, or more main ingredients gradually.",
            "Serve with a mild side; do not rely on sugar alone to remove heat.",
            "Add chilli in stages and account for spice concentrating during reduction.",
        ),
        "too watery": (
            "There is excess moisture or insufficient uncovered cooking.",
            "Cook uncovered over controlled heat, stirring as needed to prevent catching.",
            "Remove delicate cooked pieces temporarily while the sauce reduces.",
            "Add liquid gradually and monitor consistency before the final stage.",
        ),
        "too dry": (
            "Moisture evaporated too quickly or the heat was too high.",
            "Lower the heat and add a small amount of compatible warm liquid.",
            "Cover briefly to redistribute moisture, then reassess texture.",
            "Use the stated range and check earlier with observable cues.",
        ),
        "burnt": (
            "The heat was excessive, the pan was dry, or the food was left unstirred.",
            "Turn off the heat and move unburnt food to a clean pan without scraping the burnt layer.",
            "Taste before continuing; a strong burnt flavour may not be recoverable.",
            "Use lower heat, a heavier pan, and more frequent checks.",
        ),
        "undercooked": (
            "The food needed more time, gentler heat, or smaller pieces.",
            "Continue cooking at controlled heat and verify the densest piece.",
            "Add a little liquid and cover if the outside is drying before the centre cooks.",
            "Cut evenly and verify meat or fish with a food thermometer.",
        ),
        "rice too soft": (
            "The rice absorbed excess water or cooked too long.",
            "Remove from heat, uncover, and spread gently so steam can escape.",
            "Use it in a preparation where softer rice is acceptable; full reversal is unlikely.",
            "Measure water and check the grain before the maximum time.",
        ),
        "rice too hard": (
            "The rice has not absorbed enough water or heat was interrupted.",
            "Sprinkle in a small amount of hot water, cover, and cook gently for a few more minutes.",
            "Rest covered off heat, then test a grain before adding more water.",
            "Keep the lid closed during absorption and use a suitable vessel.",
        ),
        "chicken too dry": (
            "The chicken cooked too long or at excessive heat.",
            "Stop cooking and add it to a compatible sauce or moist component.",
            "Slice and serve with sauce; the lost moisture cannot be completely restored.",
            "Check earlier and use a thermometer to avoid unnecessary extra cooking.",
        ),
        "masala too raw": (
            "Aromatics or spices did not cook long enough at controlled heat.",
            "Cook gently with a small splash of water or oil, stirring until the raw aroma reduces.",
            "Keep delicate cooked ingredients aside while finishing the masala if practical.",
            "Cook aromatics until their raw aroma reduces before adding large amounts of liquid.",
        ),
        "onion burnt": (
            "The pan was too hot or the onion was not moved often enough.",
            "Remove the onion immediately and keep only pieces that do not taste bitter.",
            "Restart the onion base if bitterness is strong; burnt onion is difficult to mask.",
            "Lower the heat and stir more often as colour develops.",
        ),
    }

    @classmethod
    def solve(cls, problem):
        key = " ".join(str(problem or "").casefold().split())
        if key not in cls.PROBLEMS:
            return None
        cause, action, recovery, prevention = cls.PROBLEMS[key]
        return {
            "problem": key,
            "probable_cause": cause,
            "immediate_action": action,
            "recovery_option": recovery,
            "prevention_tip": prevention,
            "disclaimer": "Recovery depends on severity; taste and food-safety checks still apply.",
            "source": "rule-based",
        }

    @classmethod
    def supported_problems(cls):
        return list(cls.PROBLEMS)
