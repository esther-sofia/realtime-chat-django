# Real-Time Chat Application

A real-time chat application built with Django, Django Channels, WebSockets, Redis, and Celery — demonstrating asynchronous, event-driven backend architecture.

## Features

- Real-time, bidirectional messaging via WebSockets (Django Channels)
- Persistent message storage with chat history loading on join
- Redis as the Channels layer backend, enabling message broadcasting across connections
- Asynchronous background task processing with Celery (triggered on every new message)
- Django REST Framework included for future API expansion
- Django admin integration for viewing/managing stored messages

## Tech Stack

- **Backend:** Django, Django REST Framework
- **Real-time layer:** Django Channels, WebSockets, Daphne (ASGI server)
- **Message broker / Channel layer:** Redis
- **Background tasks:** Celery
- **Database:** SQLite (local development)

## Architecture Overview

1. A user connects to a chat room via WebSocket (`/ws/chat/<room_name>/`)
2. On connect, the last 20 messages for that room are loaded from the database and sent to the user
3. When a message is sent, it is:
   - Saved to the database
   - Queued as a background task via Celery (simulating a notification/logging pipeline)
   - Broadcast in real time to everyone in the room via Redis-backed channel layer
4. All connected clients in the room receive the message instantly, without polling or refreshing

## Design Decisions & Tradeoffs

- **SQLite over PostgreSQL:** used for local development simplicity. In production, PostgreSQL would be used for proper concurrent write support.
- **Daphne over Uvicorn:** Daphne is Django Channels' native ASGI server, chosen here for straightforward integration. In a production deployment at scale, Uvicorn + Gunicorn would likely offer better performance under concurrent WebSocket load.
- **Simplified auth:** users are identified by name only (no password-based login) to keep the demo focused on the real-time/async architecture. A production version would use Django's full authentication system.

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

# Run migrations
python3 manage.py migrate

# Create a superuser (optional, for admin access)
python3 manage.py createsuperuser
```

### Run the app

You'll need **three terminals** running simultaneously:

```bash
# Terminal 1: Redis (if not already running as a service)
redis-server

# Terminal 2: Django server
python3 manage.py runserver 8001

# Terminal 3: Celery worker
celery -A chatproject worker --loglevel=info
```

Visit `http://127.0.0.1:8001/chat/general/` in your browser. Open multiple tabs to test real-time messaging.

## Future Improvements

- Switch to PostgreSQL for production readiness
- Add proper user authentication
- Deploy to AWS with Docker
- Add typing indicators and read receipts
- Write automated tests for consumers and models