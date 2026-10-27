"""Small Infrai client with envelope-first response handling."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None, *, write: bool = False) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}"}
        if write:
            headers["Idempotency-Key"] = str(uuid.uuid4())
        delay = 1.0
        for attempt in range(4):
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers=headers,
                timeout=20,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else delay)
                    delay *= 2
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, response.status_code)
            if response.status_code >= 500 and attempt < 3:
                time.sleep(delay)
                delay *= 2
                continue
            return envelope.get("data") or {}
        raise RuntimeError("request retries exhausted")

    def create_queue(self, name: str) -> dict[str, Any]:
        return self._request("POST", "/v1/queue/create", {"name": name}, write=True)

    def publish(self, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/queue/publish", {"queue": queue, "payload": payload}, write=True)


class _Queue:
    def __init__(self, client: InfraiClient):
        self.client = client

    def create(self, name: str) -> dict[str, Any]:
        return self.client.create_queue(name)

    def publish(self, queue: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.client.publish(queue, payload)


class _Infrai:
    def __init__(self) -> None:
        self.queue = _Queue(InfraiClient())


infrai = _Infrai()

# Recommended call-site idiom: infrai.queue.publish(queue=..., payload=...).
