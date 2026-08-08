# AI Cooking Intelligence Architecture

## Purpose

AI Cooking Intelligence extends the existing `Recipe` and `Ingredient` system into a guided
cooking assistant. It does not replace legacy recipe steps, scaling, authentication, favorites,
or AI providers.

## Request flow

```text
Recipe page + preferences
        |
POST /api/v1/recipes/{id}/cooking-plan
        |
CookingController
        |
CookingPlanService
        |-- stored CookingStep records, when curated data exists
        `-- rule-based engines over Recipe.steps, otherwise
              |-- CookingSequenceEngine
              |-- TimingEngine
              |-- TemperatureEngine
              |-- DonenessEngine
              |-- TransformationEngine
              `-- PersonalizationEngine
        |
CookingValidationService
        |
Validated plan or a safe API error
        |
Cooking Plan / Cooking Mode UI
```

## Data model

- `recipes` and `ingredients` remain the source of truth for recipe identity and quantities.
- `recipes.steps` remains supported for backward compatibility.
- `cooking_steps` stores curated, normalized cooking guidance.
- `cooking_step_ingredients` links a structured step to existing ingredients and stores why an
  ingredient belongs at that stage.
- If a recipe has no curated structured steps, a plan is generated deterministically and marked
  `rule-based`. It is not silently written to the database.

This approach lets maintainers progressively curate high-value recipes without blocking existing
recipes or manufacturing unverified data.

## Deterministic engines

- **Sequence:** classifies the stored instruction and links only ingredients belonging to the
  current recipe. It explains timing, contribution, early/late risks, and transformation.
- **Temperature:** supplies contextual heat levels and practical ranges. Ranges are estimates, not
  universal pan-temperature facts.
- **Timing:** uses explicit recipe timing when present and conservative stage estimates otherwise.
- **Doneness:** combines appearance, colour, texture, and descriptive aroma cues. Visual progress
  is clearly identified as an estimate.
- **Transformation:** shows a beginner-friendly `before → process → after` explanation.
- **Personalization:** scales quantities deterministically and applies bounded spice, oil, and salt
  adjustments. Dietary conflicts create warnings rather than silent substitutions.
- **Troubleshooting:** provides conservative recovery guidance for known problems and never
  guarantees full recovery.

## AI boundary

AI is optional and used only for language/reasoning tasks: natural-language explanations, unknown
troubleshooting context, and context-dependent substitutions.

Deterministic code continues to own quantities, units, stored order, durations, temperature
ranges, validation, and fallback plans. AI output must match a required JSON shape. Malformed,
timed-out, or unavailable AI responses are discarded and replaced with rule-based guidance. No AI
call is made while generating an ordinary cooking plan.

## Frontend composition

The existing recipe detail route remains the entry point. `CookingIntelligencePanel` composes:

- personalization controls;
- cooking summary, heat profile, and manual timeline;
- expandable cooking steps and ingredient sequence;
- temperature, doneness, colour, texture, aroma, and transformation indicators;
- optional beginner and cooking-science explanations;
- substitutions and troubleshooting;
- mobile-friendly Cooking Mode with an independent reducer-driven timer.

Cooking Mode never advances because a timer expires. The cook must press **Done — Next Step** or
**Skip** after checking observable cues.

## Safety

Visual cues and time do not establish safety for meat or fish. Heated poultry steps advise a
thermometer reading of 74°C (165°F), and fish steps advise 63°C (145°F), following the
[USDA FSIS safe minimum internal temperature chart](https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/safe-temperature-chart).

## API surface

- `GET|POST /api/v1/recipes/{id}/cooking-plan`
- `GET /api/v1/recipes/{id}/cooking-steps`
- `POST /api/v1/cooking/troubleshoot`
- `POST /api/v1/cooking/substitute`
- `POST /api/v1/cooking/explain`

The existing `POST /api/v1/calculate` remains the quantity-scaling endpoint; no duplicate cooking
scale endpoint was added.

## Failure behavior

- Missing recipe: `404`.
- Invalid preferences or generated plan: `400`; invalid data is not shown.
- AI unavailable/malformed: deterministic fallback.
- No structured cooking rows: legacy instructions are converted at request time.
- Frontend request failure: original Ingredients & Steps remain usable, with retry UI for the plan.

## Known limitations

- Rule-based stage detection is intentionally conservative and cannot understand every compound
  instruction as deeply as a curated plan.
- Existing recipes contain combined actions; the timeline treats each stored string as one stage
  and does not model parallel preparation.
- Temperature ranges describe cooking conditions, not live sensor readings.
- The timer remains in browser memory and does not synchronize across devices.
- Curated `cooking_steps` data needs a trusted editor or future administration workflow.

## Future improvements

1. Curate structured plans for the most-used recipes.
2. Add an authenticated editor with validation previews.
3. Model parallel preparation and dependency graphs.
4. Persist user cooking progress and preferences.
5. Add offline timer notifications and accessibility-focused voice controls.
6. Add validated allergen metadata before expanding substitution automation.
