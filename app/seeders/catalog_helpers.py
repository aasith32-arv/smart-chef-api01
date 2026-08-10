def ingredient(name, quantity, unit):
    return {"name": name, "quantity": quantity, "unit": unit}


def recipe(
    name,
    family_slug,
    category,
    description,
    ingredients,
    steps,
    *,
    cuisine,
    region,
    protein="None",
    diet_type="Omnivore",
    difficulty="Medium",
    prep_time=20,
    cook_time=35,
    spice_level="Medium",
    tags=None,
    serving_size=4,
):
    return {
        "name": name,
        "family_slug": family_slug,
        "category": category,
        "description": description,
        "serving_size": serving_size,
        "image": "",
        "cuisine": cuisine,
        "region": region,
        "protein": protein,
        "diet_type": diet_type,
        "difficulty": difficulty,
        "prep_time": prep_time,
        "cook_time": cook_time,
        "spice_level": spice_level,
        "tags": tags or [],
        "ingredients": ingredients,
        "steps": steps,
    }


def biryani(
    name,
    cuisine,
    region,
    protein,
    rice,
    signatures,
    method,
    *,
    diet_type="Omnivore",
    spice_level="Medium",
    prep_time=35,
    cook_time=55,
):
    main = (
        ingredient("Mixed vegetables", 500, "g")
        if protein == "None"
        else ingredient(protein, 750 if protein not in {"Fish", "Prawn", "Egg"} else 600, "g")
    )
    if protein == "Egg":
        main = ingredient("Egg", 6, "piece")
    items = [
        ingredient(rice, 500, "g"),
        main,
        ingredient("Onion", 250, "g"),
        ingredient("Ginger garlic paste", 35, "g"),
        ingredient("Yogurt", 180, "g"),
        ingredient("Ghee", 60, "ml"),
        ingredient("Mint leaves", 20, "g"),
        ingredient("Coriander leaves", 20, "g"),
        ingredient("Salt", 12, "g"),
        *signatures,
    ]
    steps = [
        f"Rinse and soak the {rice.lower()} for 20 minutes, then drain well.",
        f"Prepare the {protein.lower() if protein != 'None' else 'vegetables'} with yogurt, ginger garlic paste, salt and the recipe spices.",
        "Fry the onions in ghee until evenly golden; reserve one third for finishing.",
        method,
        "Cook the rice only to the stage required by the regional method so the grains do not overcook during finishing.",
        "Layer or combine the rice and masala as directed, scatter mint, coriander and reserved onions, then cover tightly.",
        "Finish over low heat, rest covered for 10 minutes, and lift the rice gently from the edge before serving.",
    ]
    return recipe(
        name,
        "biryani",
        "Rice Dishes",
        f"An authentic {region} biryani distinguished by {method.rstrip('.').lower()}.",
        items,
        steps,
        cuisine=cuisine,
        region=region,
        protein=protein,
        diet_type=diet_type,
        difficulty="Advanced",
        prep_time=prep_time,
        cook_time=cook_time,
        spice_level=spice_level,
        tags=["biryani", "rice", region.casefold(), "celebration"],
    )


def curry(
    name,
    family_slug,
    primary_name,
    primary_quantity,
    cuisine,
    region,
    signatures,
    method,
    *,
    liquid=None,
    category="Curries",
    protein=None,
    diet_type="Omnivore",
    spice_level="Medium",
    prep_time=20,
    cook_time=40,
):
    items = [
        ingredient(primary_name, primary_quantity, "g"),
        ingredient("Onion", 180, "g"),
        ingredient("Ginger", 20, "g"),
        ingredient("Garlic", 20, "g"),
        ingredient("Oil", 45, "ml"),
        ingredient("Salt", 10, "g"),
        *signatures,
    ]
    if liquid:
        items.append(ingredient(liquid[0], liquid[1], liquid[2]))
    steps = [
        f"Prepare the {primary_name.lower()} in even pieces and season lightly with salt.",
        "Heat the oil and soften the onion until the raw edge disappears.",
        "Add ginger, garlic and the dry spices; cook briefly until fragrant without scorching.",
        method,
        "Add the main ingredient and turn it through the spice base so every piece is coated.",
        "Add the cooking liquid gradually and simmer at controlled heat until tender and safely cooked.",
        "Check the intended gravy texture, balance salt and acidity, then rest for 5 minutes before serving.",
    ]
    return recipe(
        name,
        family_slug,
        category,
        f"A {region} preparation with a distinct regional spice base and cooking method.",
        items,
        steps,
        cuisine=cuisine,
        region=region,
        protein=protein or primary_name,
        diet_type=diet_type,
        difficulty="Medium",
        prep_time=prep_time,
        cook_time=cook_time,
        spice_level=spice_level,
        tags=[family_slug, region.casefold(), cuisine.casefold()],
    )
