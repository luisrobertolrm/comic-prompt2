from collections.abc import Iterator

import pytest
from ai_text_config import AITextConfig
from fastapi.testclient import TestClient

from prompt_clinica.deps import get_current_admin
from prompt_clinica.main import app
from tests.conftest import _TestSession

BASE = "/admin/ai-configs"


def _payload(name: str, **extra: object) -> dict[str, object]:
    return {
        "name": name,
        "kind": "openai",
        "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3/",
        "api_key": "sk-test-abcd1234",
        "model": "seed-1-6",
        **extra,
    }


@pytest.fixture
def admin_client(client: TestClient) -> Iterator[TestClient]:
    app.dependency_overrides[get_current_admin] = lambda: object()
    with _TestSession() as s:
        s.query(AITextConfig).delete()
        s.commit()
    return client


def test_patch_active_deactivates_previous(admin_client: TestClient) -> None:
    a = admin_client.post(f"{BASE}/text", json=_payload("A", active=True)).json()
    b = admin_client.post(f"{BASE}/text", json=_payload("B")).json()

    resp = admin_client.patch(f"{BASE}/text/{b['id']}/active", json={"active": True})

    assert resp.status_code == 200
    by_id = {c["id"]: c for c in resp.json()}
    assert by_id[b["id"]]["active"] is True
    assert by_id[a["id"]]["active"] is False
    assert resp.json()[0]["id"] == b["id"]


def test_create_active_deactivates_previous(admin_client: TestClient) -> None:
    a = admin_client.post(f"{BASE}/text", json=_payload("A", active=True)).json()
    admin_client.post(f"{BASE}/text", json=_payload("B", active=True))

    configs = {c["id"]: c for c in admin_client.get(f"{BASE}/text").json()}
    assert configs[a["id"]]["active"] is False
    assert sum(c["active"] for c in configs.values()) == 1


def test_delete_active_is_blocked(admin_client: TestClient) -> None:
    a = admin_client.post(f"{BASE}/text", json=_payload("A", active=True)).json()

    assert admin_client.delete(f"{BASE}/text/{a['id']}").status_code == 409

    admin_client.patch(f"{BASE}/text/{a['id']}/active", json={"active": False})
    assert admin_client.delete(f"{BASE}/text/{a['id']}").status_code == 204


def test_update_with_null_key_keeps_key(admin_client: TestClient) -> None:
    a = admin_client.post(f"{BASE}/text", json=_payload("A")).json()
    assert a["key_hint"] == "…1234"

    resp = admin_client.put(f"{BASE}/text/{a['id']}", json=_payload("A2", api_key=None, model="seed-2"))

    assert resp.status_code == 200
    assert resp.json()["key_hint"] == "…1234"
    assert resp.json()["model"] == "seed-2"
    assert resp.json()["base_url"] == "https://ark.ap-southeast.bytepluses.com/api/v3"


def test_invalid_kind_is_rejected(admin_client: TestClient) -> None:
    resp = admin_client.post(f"{BASE}/text", json=_payload("A", kind="minimax"))
    assert resp.status_code == 422


def test_unknown_ai_type_is_404(admin_client: TestClient) -> None:
    assert admin_client.get(f"{BASE}/foo").status_code == 404


def test_response_never_contains_api_key(admin_client: TestClient) -> None:
    admin_client.post(f"{BASE}/text", json=_payload("A"))
    for config in admin_client.get(f"{BASE}/text").json():
        assert "api_key" not in config
        assert "sk-test" not in str(config)
