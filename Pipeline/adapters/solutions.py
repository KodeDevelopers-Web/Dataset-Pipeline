"""Helpers for normalizing reference solutions from dataset records."""

import json
from typing import Any, Optional


def first_solution(solutions: Any) -> Optional[str]:
    """Return the first non-empty solution from a dataset field."""
    if solutions is None:
        return None

    if isinstance(solutions, str):
        value = solutions.strip()
        if not value:
            return None
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if parsed != value:
            return first_solution(parsed)
        return value

    if isinstance(solutions, (list, tuple)):
        for solution in solutions:
            result = first_solution(solution)
            if result:
                return result
        return None

    if isinstance(solutions, dict):
        for key in ("solution", "code", "completion"):
            if key in solutions:
                result = first_solution(solutions[key])
                if result:
                    return result

    return None
