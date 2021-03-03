import random, string
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from fastingapi import main

client = TestClient(main.app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "what"}


def test_get_users():
    response = client.get("/users/")
    assert response.status_code == 200


def test_get_user_by_id():
    user_id = 1
    response = client.get("/users/"+ str(user_id))
    assert response.status_code == 200


def test_create_user():
    email = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    password =  ''.join(random.choice(string.ascii_lowercase) for i in range(10))
    payload = {"email":email, "password":password}
    response = client.post('/users/', json=payload)
    assert response.status_code == 200


def test_get_userfasts():
    user_id = 1
    response = client.get(f"/fast/{user_id}/fasts/")
    assert response.status_code == 200


def test_end_fast():
    user_id = 1
    response = client.post(f"/fast/{user_id}/end_fast/", json={})
    print(response.json())
    assert response.status_code == 200

def test_create_fast_with_duration():
    user_id = 1
    start_time = (datetime.utcnow() - timedelta(hours=23)).strftime("%Y-%m-%d %H:%M")
    payload = {"start_time":start_time, "planned_duration":24}
    print(payload)
    response = client.post(f"/fast/{user_id}/fasts/", json=payload)
    print(response.json())
    assert response.status_code == 200