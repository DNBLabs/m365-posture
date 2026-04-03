import copy

from m365_posture.redact import redact_report


def test_user_principal_name_masked_no_at_sign():
    data = {
        "userPrincipalName": "alice.contoso@contoso.onmicrosoft.com",
        "mail": "alice.contoso@contoso.com",
    }
    redacted = redact_report(data)
    assert "@" not in redacted["userPrincipalName"]
    assert redacted["userPrincipalName"] == "[REDACTED]"
    assert redacted["mail"] == "[REDACTED]"


def test_nested_dict_id_field_stable_token():
    inner_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    data = {
        "chapter": {
            "items": [
                {"displayName": "Secret User", "id": inner_id},
            ]
        }
    }
    redacted = redact_report(data)
    token = redacted["chapter"]["items"][0]["id"]
    assert token != inner_id
    assert inner_id not in str(redacted)
    assert token.startswith("[GUID-")
    assert token.endswith("]")
    again = redact_report(data)
    assert again["chapter"]["items"][0]["id"] == token


def test_display_name_redacted():
    data = {"displayName": "Jane Doe"}
    redacted = redact_report(data)
    assert redacted["displayName"] == "[REDACTED]"


def test_original_data_not_mutated():
    inner = {"id": "11111111-2222-3333-4444-555555555555"}
    data = {"wrap": inner}
    snapshot = copy.deepcopy(data)
    redact_report(data)
    assert data == snapshot
