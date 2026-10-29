import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_room_redirects_to_login_when_logged_out(client):
    response = client.get("/chat/lobby/")
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")


@pytest.mark.django_db
def test_login_page_works_and_logged_in_user_sees_room(client):
    assert client.get("/accounts/login/").status_code == 200
    User.objects.create_user(username="asha", password="pw-12345")
    response = client.post("/accounts/login/", {"username": "asha", "password": "pw-12345"})
    assert response.status_code == 302 and response.url == "/chat/lobby/"
    room = client.get("/chat/lobby/")
    assert room.status_code == 200
    assert b"Logged in as asha" in room.content