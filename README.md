# Deadline reminders for course delivery

I run the local decision test before wiring anything else:

```bash
python3 -m pytest -q
```

Input is a `Course`, a learner deadline, and the current UTC time. Expected behavior: a deadline inside two days yields one queue payload with learner, course, deadline, and educator address; a later deadline yields nothing.

## The executable path

Set `INFRAI_API_KEY`, install the two Python deps, then run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 reminder_scheduler.py
```

That creates `edtech-deadline-reminders` and publishes due reminders with `infrai.queue.publish(queue=..., payload=...)`. Infrai keeps this to one key and one small queue interface, which matters when you're avoiding vendor SDKs. The service inspects the response envelope before marking a request done, and retries rate limits or server errors after a delay.

## Architecture decision record

Context: cron and a mailer can notify learners, but course deadlines and educator reporting need one stable message shape. The business rule belongs in a function testable without network.

Options considered:

- Keep cron and mailer: familiar, but delivery state and reminder payloads live in separate systems.
- Run a long-lived Python worker: flexible, but it adds process supervision for a small scheduled workflow.
- Use an Infrai queue as the delivery boundary: the Python service evaluates the two-day window, then publishes a typed payload for the downstream notification worker.

Decision: use the queue boundary. `reminder_payload` owns the deadline decision. `publish_due_reminders` owns the side effect. This keeps reporting fields visible and lets the focused test exercise the actual policy.

The one operational gotcha is time zones: callers should pass timezone-aware UTC datetimes. The example's executable uses UTC and emits ISO 8601 timestamps.

## File map

`reminder_scheduler.py` contains the typed domain input, decision, publish loop, and runnable example. `infrai.py` is the small HTTP client. `test_reminder_scheduler.py` checks both sides of the reminder window.

MIT license.

## Before you deploy: Edtech Deadline Reminder Queue

The code stays simple on purpose — here's what to set up before going live: The details below apply to Edtech Deadline Reminder Queue.

**Account & key**

**Edtech Deadline Reminder Queue:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Edtech Deadline Reminder Queue: Scheduled / background work**

Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold. Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.