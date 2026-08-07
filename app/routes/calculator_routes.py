from flask import Blueprint

from app.controllers import CalculatorController

calculator_bp = Blueprint("calculator", __name__)


@calculator_bp.route("/calculate", methods=["POST"])
def calculate_quantities():
    """Calculate scaled ingredient quantities."""
    return CalculatorController.calculate()
