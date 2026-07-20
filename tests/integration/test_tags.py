import asyncio
import uuid

import pytest
from httpx import AsyncClient


async def test_create_tag(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags",
        json={"name": "my-tag", "description": "desc"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my-tag"
    assert data["description"] == "desc"
    assert "id" in data
    assert data["values"] == []


async def test_create_tag_with_values(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags",
        json={
            "name": "tag-nested",
            "description": "with values",
            "values": [
                {"name": "val-one", "description": "first"},
                {"name": "val-two", "description": "second"},
            ],
        },
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["values"]) == 2
    assert data["values"][0]["name"] == "val-one"
    assert data["values"][1]["name"] == "val-two"


async def test_list_tags(client: AsyncClient, user_id: uuid.UUID):
    # Create two tags
    await client.post(
        "/tags", json={"name": "tag-a"}, headers={"X-User-ID": str(user_id)}
    )
    await client.post(
        "/tags", json={"name": "tag-b"}, headers={"X-User-ID": str(user_id)}
    )
    resp = await client.get("/tags", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    names = {t["name"] for t in data["items"]}
    assert "tag-a" in names
    assert "tag-b" in names


async def test_get_tag(client: AsyncClient, user_id: uuid.UUID):
    create_resp = await client.post(
        "/tags", json={"name": "get-me"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.get(f"/tags/{tag_id}", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 200
    assert resp.json()["name"] == "get-me"


async def test_update_tag(client: AsyncClient, user_id: uuid.UUID):
    create_resp = await client.post(
        "/tags", json={"name": "update-me"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/tags/{tag_id}",
        json={"name": "updated-name", "description": "new desc"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "updated-name"
    assert resp.json()["description"] == "new desc"


async def test_delete_tag(client: AsyncClient, user_id: uuid.UUID):
    create_resp = await client.post(
        "/tags", json={"name": "delete-me"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.delete(f"/tags/{tag_id}", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 204
    # Confirm gone
    get_resp = await client.get(f"/tags/{tag_id}", headers={"X-User-ID": str(user_id)})
    assert get_resp.status_code == 404


async def test_delete_tag_cascades_values(client: AsyncClient, user_id: uuid.UUID):
    create_resp = await client.post(
        "/tags",
        json={"name": "cascade-tag", "values": [{"name": "cv1"}]},
        headers={"X-User-ID": str(user_id)},
    )
    tag_id = create_resp.json()["id"]
    resp = await client.delete(f"/tags/{tag_id}", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 204
    # Values should be gone too
    values_resp = await client.get(
        f"/tags/{tag_id}/values", headers={"X-User-ID": str(user_id)}
    )
    assert values_resp.status_code == 404


async def test_get_nonexistent_tag_returns_404(client: AsyncClient, user_id: uuid.UUID):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/tags/{fake_id}", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 404


async def test_duplicate_tag_name_returns_409(client: AsyncClient, user_id: uuid.UUID):
    await client.post(
        "/tags", json={"name": "dup-tag"}, headers={"X-User-ID": str(user_id)}
    )
    resp = await client.post(
        "/tags", json={"name": "dup-tag"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 409


async def test_different_users_can_have_same_tag_name(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    resp1 = await client.post(
        "/tags", json={"name": "shared-name"}, headers={"X-User-ID": uid1}
    )
    resp2 = await client.post(
        "/tags", json={"name": "shared-name"}, headers={"X-User-ID": uid2}
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201


async def test_user_cannot_see_other_users_tag(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    create_resp = await client.post(
        "/tags", json={"name": "private-tag"}, headers={"X-User-ID": uid1}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.get(f"/tags/{tag_id}", headers={"X-User-ID": uid2})
    assert resp.status_code == 404


async def test_missing_user_header_returns_422(client: AsyncClient):
    resp = await client.get("/tags")
    assert resp.status_code == 422


async def test_invalid_uuid_returns_422(client: AsyncClient):
    resp = await client.get("/tags", headers={"X-User-ID": "not-a-uuid"})
    assert resp.status_code == 422


async def test_invalid_name_too_short(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags", json={"name": "ab"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 422


async def test_invalid_name_uppercase(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags", json={"name": "BadName"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 422


async def test_invalid_name_spaces(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags", json={"name": "has space"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 422


async def test_pagination(client: AsyncClient, user_id: uuid.UUID):
    for i in range(5):
        await client.post(
            "/tags",
            json={"name": f"page-tag-{i:02d}"},
            headers={"X-User-ID": str(user_id)},
        )
    resp = await client.get(
        "/tags?page=1&page_size=2", headers={"X-User-ID": str(user_id)}
    )
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 5
    assert len(data["items"]) == 2


async def test_filter_by_name(client: AsyncClient, user_id: uuid.UUID):
    await client.post(
        "/tags", json={"name": "filter-alpha"}, headers={"X-User-ID": str(user_id)}
    )
    await client.post(
        "/tags", json={"name": "filter-beta"}, headers={"X-User-ID": str(user_id)}
    )
    resp = await client.get(
        "/tags?name=filter-alpha", headers={"X-User-ID": str(user_id)}
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "filter-alpha"


async def test_invalid_name_too_long(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags",
        json={"name": "a" * 65},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 422


async def test_empty_patch_body_returns_422(client: AsyncClient, user_id: uuid.UUID):
    create_resp = await client.post(
        "/tags", json={"name": "patch-empty"}, headers={"X-User-ID": str(user_id)}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/tags/{tag_id}",
        json={},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 422


async def test_nested_duplicate_value_names_rejected(
    client: AsyncClient, user_id: uuid.UUID
):
    resp = await client.post(
        "/tags",
        json={"name": "dup-values", "values": [{"name": "dup"}, {"name": "dup"}]},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 409


# --- Concurrent IntegrityError ---


async def test_concurrent_duplicate_tag_returns_409(client: AsyncClient):
    user = str(uuid.uuid4())
    results = await asyncio.gather(
        client.post(
            "/tags",
            json={"name": "concurrent-tag"},
            headers={"X-User-ID": user},
        ),
        client.post(
            "/tags",
            json={"name": "concurrent-tag"},
            headers={"X-User-ID": user},
        ),
    )
    codes = {r.status_code for r in results}
    assert codes == {201, 409}


async def test_session_usable_after_concurrent_conflict(client: AsyncClient):
    user = str(uuid.uuid4())
    await asyncio.gather(
        client.post(
            "/tags",
            json={"name": "conflict-session"},
            headers={"X-User-ID": user},
        ),
        client.post(
            "/tags",
            json={"name": "conflict-session"},
            headers={"X-User-ID": user},
        ),
    )
    resp = await client.post(
        "/tags",
        json={"name": "after-conflict"},
        headers={"X-User-ID": user},
    )
    assert resp.status_code == 201


# --- Rollback & session recovery ---


async def test_failed_nested_value_rolls_back_entire_tag(
    client: AsyncClient, user_id: uuid.UUID
):
    resp = await client.post(
        "/tags",
        json={
            "name": "rollback-tag",
            "values": [{"name": "ok-val"}, {"name": "dup"}, {"name": "dup"}],
        },
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 409
    list_resp = await client.get(
        "/tags?name=rollback-tag", headers={"X-User-ID": str(user_id)}
    )
    assert list_resp.json()["total"] == 0


async def test_session_usable_after_failed_nested_creation(
    client: AsyncClient, user_id: uuid.UUID
):
    await client.post(
        "/tags",
        json={
            "name": "fail-then-ok",
            "values": [{"name": "a"}, {"name": "a"}],
        },
        headers={"X-User-ID": str(user_id)},
    )
    resp = await client.post(
        "/tags",
        json={"name": "after-fail"},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201


# --- Cross-user mutation ---


async def test_user_cannot_update_other_users_tag(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    create_resp = await client.post(
        "/tags", json={"name": "owner-tag"}, headers={"X-User-ID": uid1}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.patch(
        f"/tags/{tag_id}",
        json={"name": "stolen"},
        headers={"X-User-ID": uid2},
    )
    assert resp.status_code == 404


async def test_user_cannot_delete_other_users_tag(client: AsyncClient):
    uid1 = str(uuid.uuid4())
    uid2 = str(uuid.uuid4())
    create_resp = await client.post(
        "/tags", json={"name": "del-protected"}, headers={"X-User-ID": uid1}
    )
    tag_id = create_resp.json()["id"]
    resp = await client.delete(f"/tags/{tag_id}", headers={"X-User-ID": uid2})
    assert resp.status_code == 404


# --- UUID path param ---


async def test_invalid_uuid_in_path_returns_422(
    client: AsyncClient, user_id: uuid.UUID
):
    resp = await client.get("/tags/not-a-uuid", headers={"X-User-ID": str(user_id)})
    assert resp.status_code == 422


# --- Description null ---


async def test_description_can_be_null(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags",
        json={"name": "null-desc", "description": None},
        headers={"X-User-ID": str(user_id)},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


async def test_description_omitted_is_null(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.post(
        "/tags", json={"name": "no-desc"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


# --- Name special characters ---


@pytest.mark.parametrize(
    "bad_name",
    ["tag@name", "tag#name", "tag!name", "tag.name", "tag name", "TAG-name"],
)
async def test_invalid_name_special_chars(
    client: AsyncClient, user_id: uuid.UUID, bad_name: str
):
    resp = await client.post(
        "/tags", json={"name": bad_name}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 422


# --- Pagination edge cases ---


async def test_pagination_page_beyond_total(client: AsyncClient, user_id: uuid.UUID):
    await client.post(
        "/tags", json={"name": "pg-one"}, headers={"X-User-ID": str(user_id)}
    )
    resp = await client.get(
        "/tags?page=999&page_size=10", headers={"X-User-ID": str(user_id)}
    )
    data = resp.json()
    assert data["items"] == []
    assert data["total"] >= 1


async def test_pagination_page_size_one(client: AsyncClient, user_id: uuid.UUID):
    for i in range(3):
        await client.post(
            "/tags",
            json={"name": f"ps-one-{i}"},
            headers={"X-User-ID": str(user_id)},
        )
    resp = await client.get(
        "/tags?page=1&page_size=1", headers={"X-User-ID": str(user_id)}
    )
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["pages"] >= 3


# --- Deterministic ordering ---


async def test_list_tags_deterministic_order(client: AsyncClient, user_id: uuid.UUID):
    for name in ["zebra", "alpha", "middle"]:
        await client.post(
            "/tags", json={"name": name}, headers={"X-User-ID": str(user_id)}
        )
    resp1 = await client.get("/tags", headers={"X-User-ID": str(user_id)})
    resp2 = await client.get("/tags", headers={"X-User-ID": str(user_id)})
    names1 = [t["name"] for t in resp1.json()["items"]]
    names2 = [t["name"] for t in resp2.json()["items"]]
    assert names1 == names2


# --- Error response format ---


async def test_error_response_format(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.get(
        "/tags/" + str(uuid.uuid4()), headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 404
    body = resp.json()
    assert "type" in body
    assert "title" in body
    assert body["status"] == 404
    assert "detail" in body
    assert "instance" in body


async def test_conflict_error_response_format(client: AsyncClient, user_id: uuid.UUID):
    await client.post(
        "/tags", json={"name": "conflict-fmt"}, headers={"X-User-ID": str(user_id)}
    )
    resp = await client.post(
        "/tags", json={"name": "conflict-fmt"}, headers={"X-User-ID": str(user_id)}
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["status"] == 409
    assert body["title"] == "Conflict"


# --- Request ID ---


async def test_request_id_returned_in_header(client: AsyncClient, user_id: uuid.UUID):
    resp = await client.get("/tags", headers={"X-User-ID": str(user_id)})
    assert "x-request-id" in resp.headers
    assert len(resp.headers["x-request-id"]) > 0


async def test_request_id_echoed_from_client(client: AsyncClient, user_id: uuid.UUID):
    custom_id = "my-req-id-123"
    resp = await client.get(
        "/tags",
        headers={"X-User-ID": str(user_id), "X-Request-ID": custom_id},
    )
    assert resp.headers["x-request-id"] == custom_id


# --- Tag response includes values ---


async def test_tag_response_includes_values_list(
    client: AsyncClient, user_id: uuid.UUID
):
    resp = await client.post(
        "/tags",
        json={
            "name": "with-vals",
            "values": [{"name": "val-one"}, {"name": "val-two"}],
        },
        headers={"X-User-ID": str(user_id)},
    )
    data = resp.json()
    assert isinstance(data["values"], list)
    assert len(data["values"]) == 2
    assert {v["name"] for v in data["values"]} == {"val-one", "val-two"}
