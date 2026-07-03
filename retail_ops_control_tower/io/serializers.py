"""Dataclass <-> dict serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any


def to_dict(obj: Any) -> Any:
    """Convert a dataclass instance to a dict, handling nested dataclasses."""
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


def from_dict(cls: type, data: dict) -> Any:
    """Reconstruct a dataclass instance from a dict."""
    if not is_dataclass(cls):
        return data
    import inspect
    sig = inspect.signature(cls)
    kwargs = {}
    for name, param in sig.parameters.items():
        if name in data:
            kwargs[name] = data[name]
    return cls(**kwargs)
