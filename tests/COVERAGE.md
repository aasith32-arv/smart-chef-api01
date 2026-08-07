# Backend test coverage snapshot (Phase 1)

Generated with:

```bash
pytest --cov=app.services --cov-report=term-missing
```

## Results

| Module | Coverage |
|--------|----------|
| `auth_service.py` | **90%** |
| `calculator_service.py` | **92%** |
| `favorite_service.py` | **100%** |
| `recommendation_service.py` | **100%** |
| Services package overall | 56% (includes untested AI / recipe CRUD helpers) |

**32 passed** service/auth tests.

Targeted Phase 1 modules (calculator, recommendation, auth, favorite) are all ≥ 90%.
