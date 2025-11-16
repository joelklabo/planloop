"""Tests for schema describe helpers."""
from __future__ import annotations

from planloop.core import describe


def test_state_schema_contains_top_level_properties():
    schema = describe.state_schema()
    assert schema["title"] == "SessionState"
    assert "properties" in schema
    assert "tasks" in schema["properties"]


def test_update_schema_contains_expected_fields():
    schema = describe.update_schema()
    props = schema.get("properties", {})
    assert "session" in props
    assert "tasks" in props
    assert props["tasks"]["type"] == "array"


def test_describe_payload_structure():
    payload = describe.describe_payload()
    assert set(payload.keys()) == {"state_schema", "update_schema", "enums", "error_codes", "usage_hints"}
    assert "now_reasons" in payload["enums"]
