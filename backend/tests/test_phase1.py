from tests.conftest import OTHER_USER_ID, TEST_USER_ID, auth_headers


def test_get_location_not_set(client):
    response = client.get("/v1/users/location", headers=auth_headers())
    assert response.status_code == 404


def test_set_and_get_location(client):
    payload = {"city": "Bangalore", "state": "Karnataka", "pincode": "560001"}
    create = client.post("/v1/users/location", json=payload, headers=auth_headers())
    assert create.status_code == 201
    assert create.json()["city"] == "Bangalore"

    get_resp = client.get("/v1/users/location", headers=auth_headers())
    assert get_resp.status_code == 200
    assert get_resp.json()["pincode"] == "560001"


def test_update_location(client):
    client.post(
        "/v1/users/location",
        json={"city": "Mumbai", "state": "Maharashtra", "pincode": "400001"},
        headers=auth_headers(),
    )
    update = client.post(
        "/v1/users/location",
        json={"city": "Pune", "state": "Maharashtra", "pincode": "411001"},
        headers=auth_headers(),
    )
    assert update.status_code == 201
    assert update.json()["city"] == "Pune"


def test_create_usl_item(client):
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(),
    )
    response = client.post(
        "/v1/usl/items",
        json={"raw_intent": "AirPods", "priority": 2},
        headers=auth_headers(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["raw_intent"] == "AirPods"
    assert data["status"] == "pending"
    assert data["priority"] == 2


def test_list_usl_items_with_filter(client):
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(),
    )
    client.post("/v1/usl/items", json={"raw_intent": "Dog Food"}, headers=auth_headers())
    item = client.post("/v1/usl/items", json={"raw_intent": "Face Wash"}, headers=auth_headers()).json()
    client.patch(
        f"/v1/usl/items/{item['item_id']}",
        json={"status": "purchased"},
        headers=auth_headers(),
    )

    pending = client.get("/v1/usl/items?status=pending", headers=auth_headers())
    assert pending.status_code == 200
    assert pending.json()["total"] == 1

    purchased = client.get("/v1/usl/items?status=purchased", headers=auth_headers())
    assert purchased.json()["total"] == 1

    all_items = client.get("/v1/usl/items?status=all", headers=auth_headers())
    assert all_items.json()["total"] == 2


def test_update_usl_item(client):
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(),
    )
    created = client.post(
        "/v1/usl/items",
        json={"raw_intent": "Moisturizer"},
        headers=auth_headers(),
    ).json()

    updated = client.patch(
        f"/v1/usl/items/{created['item_id']}",
        json={"raw_intent": "Cetaphil Moisturizer", "status": "saved_for_later", "priority": 1},
        headers=auth_headers(),
    )
    assert updated.status_code == 200
    data = updated.json()
    assert data["raw_intent"] == "Cetaphil Moisturizer"
    assert data["status"] == "saved_for_later"


def test_delete_usl_item(client):
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(),
    )
    created = client.post(
        "/v1/usl/items",
        json={"raw_intent": "Bluetooth Earbuds"},
        headers=auth_headers(),
    ).json()

    deleted = client.delete(f"/v1/usl/items/{created['item_id']}", headers=auth_headers())
    assert deleted.status_code == 204

    get_resp = client.patch(
        f"/v1/usl/items/{created['item_id']}",
        json={"raw_intent": "Updated"},
        headers=auth_headers(),
    )
    assert get_resp.status_code == 404


def test_usl_item_user_scoping(client):
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(TEST_USER_ID),
    )
    created = client.post(
        "/v1/usl/items",
        json={"raw_intent": "Private item"},
        headers=auth_headers(TEST_USER_ID),
    ).json()

    other_user = client.get(
        f"/v1/usl/items?status=all",
        headers=auth_headers(OTHER_USER_ID),
    )
    assert other_user.json()["total"] == 0

    forbidden = client.patch(
        f"/v1/usl/items/{created['item_id']}",
        json={"raw_intent": "Hacked"},
        headers=auth_headers(OTHER_USER_ID),
    )
    assert forbidden.status_code == 404


def test_invalid_pincode(client):
    response = client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "5600"},
        headers=auth_headers(),
    )
    assert response.status_code == 422
