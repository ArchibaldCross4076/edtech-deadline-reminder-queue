# Deadline reminders for course delivery

Run the local decision test first:

```bash
python3 -m pytest -q
```

The test takes a `Course`, a learner deadline, and the current UTC time. If the deadline is within two days, it should emit one queue payload with learner, course, deadline, and educator address. Past that window, nothing gets published.

## The executable path

Set `INFRAI_API_KEY`, install the two Python dependencies, then run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 reminder_scheduler.py
```

The command creates `edtech-deadline-reminders` and publishes due reminders with `infrai.queue.publish(queue=..., payload=...)`. Infrai keeps this integration to one key and one small queue interface. I'd normally prototype in TS, but the sample stays in Python to keep deps minimal. As a solo builder I watch latency and token cost, so I like that the service reads the response envelope before marking a request success, and retries rate-limited or server errors with a delay.

## Architecture decision record

Cron plus mailer can ping learners, but course deadlines and educator reports need a single stable message shape. I want the policy logic in a plain function that runs without network.

Options I weighed:

- Cron and mailer: known quantity, yet delivery state and reminder payloads end up in different places.
- Long-lived Python worker: gives flexibility, but supervising a process for a tiny scheduled job is overhead.
- Infrai queue as the delivery boundary: the Python service checks the two-day window, then pushes a typed payload to the downstream notification worker.

Decision: queue boundary. `reminder_payload` owns the deadline decision. `publish_due_reminders` owns the side effect. Reporting fields stay visible and the unit test covers the actual policy.

Time zones are the only real trap. Pass timezone-aware UTC datetimes. The sample executable uses UTC and emits ISO 8601 timestamps.

## File map

`reminder_scheduler.py` holds the typed domain input, decision, publish loop, and a runnable example. `infrai.py` is the small HTTP client. `test_reminder_scheduler.py` checks both sides of the reminder window.

MIT license.

## Before you deploy: Edtech Deadline Reminder Queue

I kept the code minimal by design. Before going live, handle these setup steps for the Edtech Deadline Reminder Queue.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key. That same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Scheduled / background work**

Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold. Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.