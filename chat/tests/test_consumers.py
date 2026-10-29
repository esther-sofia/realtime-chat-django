import pytest
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser, User
from chat.consumers import ChatConsumer
from chat.models import Message

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def in_memory_layer(settings, mocker):
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    mocker.patch("chat.consumers.notify_new_message")          # no real Celery


def communicator_for(user):
    app = ChatConsumer.as_asgi()
    c = WebsocketCommunicator(app, "/ws/chat/lobby/")
    c.scope["user"] = user
    c.scope["url_route"] = {"kwargs": {"room_name": "lobby"}}
    return c


async def test_anonymous_user_is_rejected():
    c = communicator_for(AnonymousUser())
    connected, _ = await c.connect()
    assert connected is False


async def test_sender_comes_from_login_not_from_browser():
    asha = await User.objects.acreate(username="asha")
    c = communicator_for(asha)
    connected, _ = await c.connect()
    assert connected
    await c.send_json_to({"message": "hi", "sender": "ravi"})   # tries to pretend to be Ravi
    reply = await c.receive_json_from()
    assert reply == {"message": "hi", "sender": "asha"}
    saved = await Message.objects.select_related("sender").aget()
    assert saved.sender.username == "asha"
    await c.disconnect()