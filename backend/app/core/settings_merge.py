from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Merge patch into base recursively (dicts only)."""
    out = deepcopy(base) if base else {}
    for key, value in patch.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = deepcopy(value)
    return out


def settings_from_patch_model(model: Any) -> dict[str, Any]:
    """Pydantic model → dict excluding unset/None."""
    if model is None:
        return {}
    return model.model_dump(exclude_unset=True, exclude_none=True)
