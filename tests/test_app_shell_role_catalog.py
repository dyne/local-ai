from __future__ import annotations

from local_ai.slices.app_shell.role_catalog import list_local_ai_roles, role_catalog_response


def test_list_local_ai_roles_has_expected_order_and_shape() -> None:
    roles = list_local_ai_roles()

    assert [role.id for role in roles] == ["voice", "documents", "ocr"]
    assert roles[0].status == "available"
    assert roles[0].primary_action == "Start recording"
    assert roles[1].status == "planned"
    assert roles[2].status == "planned"


def test_role_catalog_response_serializes_roles() -> None:
    payload = role_catalog_response()

    assert "roles" in payload
    assert isinstance(payload["roles"], list)
    assert payload["roles"][0]["id"] == "voice"
    assert payload["roles"][1]["route"] == "documents"
    assert payload["roles"][2]["label"] == "OCR"

