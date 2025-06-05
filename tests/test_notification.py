import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import NotificationSystem

def test_send_telegram_message(monkeypatch):
    calls = []
    def fake_post(url, json):
        calls.append((url, json))
        class Resp:
            def raise_for_status(self):
                pass
        return Resp()
    monkeypatch.setattr(requests, "post", fake_post)
    notifier = NotificationSystem("token", "1,2")
    notifier.send_telegram_message("hello")
    assert len(calls) == 2
    assert calls[0][0] == "https://api.telegram.org/bottoken/sendMessage"
    assert calls[0][1]["chat_id"] == "1"
    assert calls[0][1]["text"] == "hello"

def test_notify_new_listing_only_once(monkeypatch):
    sent = []
    def fake_send(msg):
        sent.append(msg)
    notifier = NotificationSystem("token", "1")
    monkeypatch.setattr(notifier, "send_telegram_message", fake_send)
    listing = {
        "id": "abc",
        "title": "t",
        "price": "p",
        "address": "a",
        "url": "u",
        "source": "s",
    }
    notifier.notify_new_listing(listing)
    notifier.notify_new_listing(listing)
    assert len(sent) == 1
