# Real-Time Chat Application

A room-based, real-time chat backend built with Django, Django Channels, WebSockets, Redis and Celery. Users log in, join a room, and see each other's messages instantly over a persistent WebSocket connection, without polling or refreshing.

## Features

- Real-time, two-way messaging over WebSockets (Django Channels)
- Login required: the sender of every message is the authenticated user, taken from the session, never from data the browser sends
- Anonymous WebSocket connections are rejected during the handshake
- Message history: the last 20 messages of a room are sent when a user joins
- Redis channel layer, so messages reach every connection in a room, across processes
- Background task processing with Celery, triggered on every new message
- Automated tests for the WebSocket consumer and the views (pytest)

## Tech Stack

- **Backend:** Python, Django
- **Real-time layer:** Django Channels, WebSockets, Daphne (ASGI server)
- **Channel layer and Celery broker:** Redis
- **Background tasks:** Celery
- **Database:** SQLite (local development)
- **Testing:** pytest, pytest-django, pytest-asyncio, pytest-mock, Channels' WebsocketCommunicator

## How It Works

1. A user opens `/chat/<room_name>/`. The page requires login, so logged-out users are redirected to the login page first.
2. The page's JavaScript opens a WebSocket to `/ws/chat/<room_name>/`. The browser sends the session cookie with the handshake.
3. `ProtocolTypeRouter` sends the WebSocket through `AuthMiddlewareStack`, which reads the session and puts the logged-in user in the scope, then `URLRouter` routes it to `ChatConsumer`.
4. In `connect`, anonymous users are rejected. Authenticated users join the room's group, and the last 20 messages are sent to them.
5. When a user sends a message, the consumer:
   - takes the sender from the logged-in user
   - saves the message to the database (via `database_sync_to_async`, so the ORM doesn't block the event loop)
   - queues a Celery task
   - broadcasts the message to the room's group through the Redis channel layer
6. Every connection in the room receives the message instantly.

## Design Decisions and Trade-offs

- **Identity from authentication:** the consumer uses `self.scope["user"]` from `AuthMiddlewareStack` and ignores any sender name in the message. An earlier version trusted a name typed in the browser, which allowed impersonation; this was fixed and is covered by tests.
- **SQLite over PostgreSQL:** chosen for local development simplicity. SQLite locks the database on each write, so a production version would use PostgreSQL.
- **Daphne as the ASGI server:** Daphne is the server maintained by the Django Channels project, and adding it to `INSTALLED_APPS` lets `runserver` serve ASGI directly in development. Uvicorn is a common alternative.

## Running Locally

### Prerequisites

- Python 3.10+
- Redis installed and running locally

### Setup

```bash
# Clone the repository
git clone https://github.com/esther-sofia/realtime-chat-django.git
cd realtime-chat-django

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file with a secret key
echo "DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" > .env

# Set up the database
python3 manage.py migrate

# Create a user to log in with (run twice to create two users)
python3 manage.py createsuperuser
```

### Run the app

```bash
# Terminal 1: Redis (or: brew services start redis)
redis-server

# Terminal 2: Django server (Daphne, via runserver)
python3 manage.py runserver

# Terminal 3 (optional): Celery worker
celery -A chatproject worker --loglevel=info
```

Visit `http://127.0.0.1:8000/chat/lobby/` and log in. To test two users chatting, log in as a second user in a private window: tabs in the same window share one login.

## Running the Tests

```bash
pytest -v
```

The tests don't need Redis or the server running: they use an in-memory channel layer and a mocked Celery task.

- **Consumer tests** (`chat/tests/test_consumers.py`), using Channels' `WebsocketCommunicator`:
  - an anonymous user's WebSocket connection is rejected
  - a logged-in user who sends a message claiming to be someone else still has it broadcast and saved under their own name
- **View tests** (`chat/tests/test_views.py`):
  - a logged-out user is redirected to the login page
  - logging in works, and a logged-in user sees the room

## Future Improvements

- Render messages with `textContent` instead of `innerHTML`, to prevent cross-site scripting
- Room membership, so users can only join rooms they belong to
- Rate limiting on messages
- PostgreSQL for production
- Containerise with Docker and deploy
