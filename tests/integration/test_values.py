import asyncio
import uuid

import pytest
from httpx import AsyncClient


async def test_create_value(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "val-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "my-value", "description": "val desc"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my-value"
    assert data["description"] == "val desc"


async def test_list_values(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "list-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "lv-a"},
        headers={"X-User-ID": str(user_id)},
    )
    await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "lv-b"},
        headers={"X-User-ID": str(user_id)},
    )
    resp = await client.get(
        f"/v1/tags/{tag_id}/values", headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 200
    names = {v["name"] for v in resp.json()}
    assert "lv-a" in names
    assert "lv-b" in names


async def test_get_value(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "get-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "get-val"},
        headers={"X-User-ID": str(user_id)},
    )
    val_id = val_resp.json()["id"]
    resp = await client.get(
        f"/v1/tags/{tag_id}/values/{val_id}", headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "get-val"


async def test_update_value(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "upd-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "upd-val"},
        headers={"X-User-ID": str(user_id)},
    )
    val_id = val_resp.json()["id"]
    resp = await client.patch(
        f"/v1/tags/{tag_id}/values/{val_id}",
        json={"name": "updated-val"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "updated-val"


async def test_delete_value(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "del-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "del-val"},
        headers={"X-User-ID": str(user_id)},
    )
    val_id = val_resp.json()["id"]
    resp = await client.delete(
        f"/v1/tags/{tag_id}/values/{val_id}", headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 204
    get_resp = await client.get(
        f"/v1/tags/{tag_id}/values/{val_id}", headers={"X-User-ID": str(user_id)}
    )
    assert get_resp.status_code == 404


async def test_value_nonexistent_tag_returns_404(
    client: AsyncClient, user_id: uuid.UUID
):
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/v1/tags/{fake_id}/values", headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 404


async def test_value_cross_user_access_denied(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    tag_resp = await client.post(
        "/v1/tags", json={"name": "cross-tag"}, headers={"X-User-ID": uid1}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "cross-val"},
        headers={"X-User-ID": uid1},
    )
    val_id = val_resp.json()["id"]
    resp = await client.get(
        f"/v1/tags/{tag_id}/values/{val_id}", headers={"X-User-ID": uid2}
    )
    assert resp.status_code == 404


async def test_duplicate_value_name_in_same_tag_returns_409(
    client: AsyncClient, user_id: uuid.UUID
):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "dup-val-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "dup-val"},
        headers={"X-User-ID": str(user_id)},
    )
    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "dup-val"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 409


async def test_empty_patch_body_returns_422(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "patch-parent"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "patch-val"},
        headers={"X-User-ID": str(user_id)},
    )
    val_id = val_resp.json()["id"]
    resp = await client.patch(
        f"/v1/tags/{tag_id}/values/{val_id}",
        json={},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 422


async def test_same_value_name_in_different_tags_allowed(
    client: AsyncClient, user_id: uuid.UUID
):
    tag1 = await client.post(
        "/v1/tags", json={"name": "val-parent-1"}, headers={"X-User-ID": str(user_id)}
    )
    tag2 = await client.post(
        "/v1/tags", json={"name": "val-parent-2"}, headers={"X-User-ID": str(user_id)}
    )
    resp1 = await client.post(
        f"/v1/tags/{tag1.json()['id']}/values",
        json={"name": "shared-val"},
        headers={"X-User-ID": str(user_id)},
    )
    resp2 = await client.post(
        f"/v1/tags/{tag2.json()['id']}/values",
        json={"name": "shared-val"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201


# --- Value name validation ---


@pytest.mark.parametrize(
    "bad_name",
    ["ab", "A", "tag@val", "tag#val", "tag.val", "tag val", "A" * 65],
)
async def test_invalid_value_name(
    client: AsyncClient, user_id: uuid.UUID, bad_name: str
):
    tag_resp = await client.post(
        "/v1/tags",
        json={"name": "valvalid-parent"},
        headers={"X-User-ID": str(user_id)},
    )
    tag_id = tag_resp.json()["id"]
    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": bad_name},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 422


# --- Description null ---


async def test_value_description_can_be_null(client: AsyncClient, user_id: uuid.UUID):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "null-vdesc"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "v-null-desc", "description": None},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


async def test_value_description_omitted_is_null(
    client: AsyncClient, user_id: uuid.UUID
):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "vno-desc"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]
    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "v-omitted"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


# --- Cross-user value mutation ---


async def test_user_cannot_update_other_users_value(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    tag_resp = await client.post(
        "/v1/tags", json={"name": "owner-vtag"}, headers={"X-User-ID": uid1}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "protected-val"},
        headers={"X-User-ID": uid1},
    )
    val_id = val_resp.json()["id"]
    resp = await client.patch(
        f"/v1/tags/{tag_id}/values/{val_id}",
        json={"name": "stolen-val"},
        headers={"X-User-ID": uid2},
    )
    assert resp.status_code == 404


async def test_user_cannot_delete_other_users_value(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    tag_resp = await client.post(
        "/v1/tags", json={"name": "del-vtag"}, headers={"X-User-ID": uid1}
    )
    tag_id = tag_resp.json()["id"]
    val_resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "del-protected-val"},
        headers={"X-User-ID": uid1},
    )
    val_id = val_resp.json()["id"]
    resp = await client.delete(
        f"/v1/tags/{tag_id}/values/{val_id}", headers={"X-User-ID": uid2}
    )
    assert resp.status_code == 404


# --- Concurrent IntegrityError ---


async def test_concurrent_duplicate_value_returns_409(
    client: AsyncClient, user_id: uuid.UUID
):
    tag_resp = await client.post(
        "/v1/tags", json={"name": "conc-val-tag"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = tag_resp.json()["id"]

    results = await asyncio.gather(
        client.post(
            f"/v1/tags/{tag_id}/values",
            json={"name": "concurrent-value"},
            headers={"X-User-ID": str(user_id)},
        ),
        client.post(
            f"/v1/tags/{tag_id}/values",
            json={"name": "concurrent-value"},
            headers={"X-User-ID": str(user_id)},
        ),
    )

    codes = {r.status_code for r in results}
    assert codes == {201, 409}


async def test_session_usable_after_value_concurrent_conflict(
    client: AsyncClient, user_id: uuid.UUID
):
    tag_resp = await client.post(
        "/v1/tags",
        json={"name": "val-session-recovery"},
        headers={"X-User-ID": str(user_id)},
    )
    tag_id = tag_resp.json()["id"]

    await asyncio.gather(
        client.post(
            f"/v1/tags/{tag_id}/values",
            json={"name": "crash-val"},
            headers={"X-User-ID": str(user_id)},
        ),
        client.post(
            f"/v1/tags/{tag_id}/values",
            json={"name": "crash-val"},
            headers={"X-User-ID": str(user_id)},
        ),
    )

    resp = await client.post(
        f"/v1/tags/{tag_id}/values",
        json={"name": "after-crash"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
