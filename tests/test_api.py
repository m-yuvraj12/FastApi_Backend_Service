from app.services import fcm
from tests.conftest import EMAIL, PASSWORD, TOKEN_A


def test_register_login_me(client):
    r = client.post("/auth/register", json={"email": "Bob@Example.com", "password": PASSWORD})
    assert r.status_code == 201 and r.json()["email"] == "bob@example.com"
    assert "password" not in r.text and "hashed" not in r.text

    assert client.post("/auth/register", json={"email": "bob@example.com", "password": PASSWORD}).status_code == 409
    assert client.post("/auth/register", json={"email": "bad", "password": PASSWORD}).status_code == 422
    assert client.post("/auth/register", json={"email": "c@example.com", "password": "short"}).status_code == 422

    assert client.post("/auth/login", data={"username": "bob@example.com", "password": "wrong-pass"}).status_code == 401
    tok = client.post("/auth/login", data={"username": "bob@example.com", "password": PASSWORD}).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert me.status_code == 200 and me.json()["email"] == "bob@example.com"


def test_endpoints_require_auth(client):
    for method, path in [("get", "/notifications"), ("post", "/notifications/send"), ("put", "/devices")]:
        assert getattr(client, method)(path).status_code == 401
    assert client.get("/notifications", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_send_persist_and_list(client, auth, fake_fcm):
    assert client.put("/devices", json={"fcm_token": TOKEN_A, "name": "Pixel"}, headers=auth).status_code == 200
    r = client.post("/notifications/send", json={"title": "Hi", "body": "There", "data": {"k": "v"}}, headers=auth)
    assert r.status_code == 201, r.text
    assert fake_fcm[0]["tokens"] == [TOKEN_A]
    assert r.json()["delivered_count"] == 1

    lst = client.get("/notifications", headers=auth).json()
    assert lst["total"] == 1 and lst["items"][0]["title"] == "Hi" and lst["items"][0]["data"] == {"k": "v"}
    assert client.get(f"/notifications/{r.json()['id']}", headers=auth).status_code == 200


def test_send_validation_and_no_device(client, auth, fake_fcm):
    assert client.post("/notifications/send", json={"title": "", "body": "x"}, headers=auth).status_code == 422
    assert client.post("/notifications/send", json={"title": "t"}, headers=auth).status_code == 422
    r = client.post("/notifications/send", json={"title": "t", "body": "b"}, headers=auth)
    assert r.status_code == 400 and not fake_fcm


def test_failed_send_not_persisted(client, auth, monkeypatch):
    monkeypatch.setattr(fcm, "send_to_tokens", lambda t, *a: [fcm.SendResult(t[0], error="boom")])
    r = client.post("/notifications/send", json={"title": "t", "body": "b", "device_token": TOKEN_A}, headers=auth)
    assert r.status_code == 502
    assert client.get("/notifications", headers=auth).json()["total"] == 0


def test_fcm_not_configured_returns_503(client, auth, monkeypatch):
    def boom(*a):
        raise fcm.FCMNotConfigured("missing")
    monkeypatch.setattr(fcm, "send_to_tokens", boom)
    r = client.post("/notifications/send", json={"title": "t", "body": "b", "device_token": TOKEN_A}, headers=auth)
    assert r.status_code == 503


def test_users_only_see_own_notifications(client, auth, fake_fcm):
    client.post("/notifications/send", json={"title": "mine", "body": "b", "device_token": TOKEN_A}, headers=auth)
    nid = client.get("/notifications", headers=auth).json()["items"][0]["id"]

    client.post("/auth/register", json={"email": "eve@example.com", "password": PASSWORD})
    tok = client.post("/auth/login", data={"username": "eve@example.com", "password": PASSWORD}).json()["access_token"]
    eve = {"Authorization": f"Bearer {tok}"}
    assert client.get("/notifications", headers=eve).json()["total"] == 0
    assert client.get(f"/notifications/{nid}", headers=eve).status_code == 404
