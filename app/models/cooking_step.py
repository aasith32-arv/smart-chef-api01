from app.extensions import db


class CookingStep(db.Model):
    """Curated cooking intelligence attached to the existing recipe system."""

    __tablename__ = "cooking_steps"
    __table_args__ = (
        db.UniqueConstraint("recipe_id", "step_number", name="uq_recipe_cooking_step"),
    )

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(
        db.Integer,
        db.ForeignKey("recipes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    instruction = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=True)
    minimum_duration = db.Column(db.Integer, nullable=True)
    maximum_duration = db.Column(db.Integer, nullable=True)
    heat_level = db.Column(db.String(30), nullable=True)
    temperature_min = db.Column(db.Integer, nullable=True)
    temperature_max = db.Column(db.Integer, nullable=True)
    visual_cue = db.Column(db.Text, nullable=True)
    colour_stage = db.Column(db.String(120), nullable=True)
    texture_cue = db.Column(db.Text, nullable=True)
    aroma_cue = db.Column(db.Text, nullable=True)
    transformation_before = db.Column(db.Text, nullable=True)
    transformation_process = db.Column(db.Text, nullable=True)
    transformation_after = db.Column(db.Text, nullable=True)
    purpose = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.JSON, nullable=False, default=list)
    warnings = db.Column(db.JSON, nullable=False, default=list)
    common_mistakes = db.Column(db.JSON, nullable=False, default=list)
    correction = db.Column(db.Text, nullable=True)
    scientific_explanation = db.Column(db.Text, nullable=True)
    critical = db.Column(db.Boolean, nullable=False, default=False)
    source = db.Column(db.String(30), nullable=False, default="curated")

    recipe = db.relationship("Recipe", back_populates="cooking_steps")
    ingredient_additions = db.relationship(
        "CookingStepIngredient",
        back_populates="step",
        cascade="all, delete-orphan",
        lazy="joined",
        order_by="CookingStepIngredient.addition_order",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "step_number": self.step_number,
            "title": self.title,
            "instruction": self.instruction,
            "duration": self.duration,
            "minimum_duration": self.minimum_duration,
            "maximum_duration": self.maximum_duration,
            "heat_level": self.heat_level,
            "temperature_min": self.temperature_min,
            "temperature_max": self.temperature_max,
            "visual_cue": self.visual_cue,
            "colour_stage": self.colour_stage,
            "texture_cue": self.texture_cue,
            "aroma_cue": self.aroma_cue,
            "transformation": {
                "before": self.transformation_before,
                "process": self.transformation_process,
                "after": self.transformation_after,
            },
            "purpose": self.purpose,
            "benefits": self.benefits or [],
            "warnings": self.warnings or [],
            "common_mistakes": self.common_mistakes or [],
            "correction": self.correction,
            "scientific_explanation": self.scientific_explanation,
            "critical": self.critical,
            "source": self.source,
            "ingredients": [item.to_dict() for item in self.ingredient_additions],
        }


class CookingStepIngredient(db.Model):
    """An ingredient addition and the reason it belongs at a cooking stage."""

    __tablename__ = "cooking_step_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    cooking_step_id = db.Column(
        db.Integer,
        db.ForeignKey("cooking_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_id = db.Column(
        db.Integer,
        db.ForeignKey("ingredients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ingredient_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    addition_order = db.Column(db.Integer, nullable=False, default=1)
    why_now = db.Column(db.Text, nullable=True)
    contribution = db.Column(db.Text, nullable=True)
    added_too_early = db.Column(db.Text, nullable=True)
    added_too_late = db.Column(db.Text, nullable=True)
    expected_transformation = db.Column(db.Text, nullable=True)
    visual_cue = db.Column(db.Text, nullable=True)
    aroma_cue = db.Column(db.Text, nullable=True)
    texture_cue = db.Column(db.Text, nullable=True)

    step = db.relationship("CookingStep", back_populates="ingredient_additions")
    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id": self.ingredient_id,
            "name": self.ingredient_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "addition_order": self.addition_order,
            "why_now": self.why_now,
            "contribution": self.contribution,
            "added_too_early": self.added_too_early,
            "added_too_late": self.added_too_late,
            "expected_transformation": self.expected_transformation,
            "visual_cue": self.visual_cue,
            "aroma_cue": self.aroma_cue,
            "texture_cue": self.texture_cue,
        }
