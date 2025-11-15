"""Prompt and message loader utilities."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Tuple

import yaml

TEMPLATES_PACKAGE = "planloop.templates"


@dataclass(frozen=True)
class TemplateDoc:
    metadata: dict
    body: str


def _split_front_matter(text: str) -> Tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    _, front, rest = parts
    metadata = yaml.safe_load(front) or {}
    body = rest.lstrip("\n")
    return metadata, body


def _read_text(path: str) -> str:
    base = resources.files(TEMPLATES_PACKAGE)
    return base.joinpath(path).read_text(encoding="utf-8")


def _load_resource(path: str) -> TemplateDoc:
    data = _read_text(path)
    metadata, body = _split_front_matter(data)
    return TemplateDoc(metadata=metadata, body=body)


@lru_cache(maxsize=None)
def load_prompt(prompt_set: str, kind: str) -> TemplateDoc:
    filename = f"{kind}.prompt.md"
    path = f"prompts/{prompt_set}/{filename}"
    return _load_resource(path)


@lru_cache(maxsize=None)
def load_message(name: str) -> TemplateDoc:
    filename = f"{name}.md"
    path = f"messages/{filename}"
    return _load_resource(path)


__all__ = ["TemplateDoc", "load_prompt", "load_message"]
