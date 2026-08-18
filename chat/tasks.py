from celery import shared_task

@shared_task
def notify_new_message(sender_name, room_name, message_content):
    print(f"[Background Task] New message in '{room_name}' from {sender_name}: {message_content}")
    return f"Notification processed for message in {room_name}"