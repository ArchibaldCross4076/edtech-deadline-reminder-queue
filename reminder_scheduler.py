"""Schedule deadline reminders for a course delivery team."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from infrai import InfraiClient


@dataclass(frozen=True)
class Course:
    course_id: str
    title: str
    educator_email: str


@dataclass(frozen=True)
class LearnerDeadline:
    learner_id: str
    course_id: str
    deadline: datetime


def reminder_payload(course: Course, deadline: LearnerDeadline, now: datetime, lead: timedelta = timedelta(days=2)) -> dict[str, Any] | None:
    """Return one reminder only while the deadline is inside the lead window."""
    if deadline.course_id != course.course_id:
        return None
    if not now <= deadline.deadline <= now + lead:
        return None
    return {
        "learner_id": deadline.learner_id,
        "course_id": course.course_id,
        "course_title": course.title,
        "deadline": deadline.deadline.isoformat(),
        "educator_email": course.educator_email,
    }


def publish_due_reminders(client: InfraiClient, queue: str, course: Course, deadlines: list[LearnerDeadline], now: datetime) -> int:
    published = 0
    for deadline in deadlines:
        payload = reminder_payload(course, deadline, now)
        if payload is not None:
            client.publish(queue, payload)
            published += 1
    return published


def main() -> None:
    now = datetime.now(timezone.utc)
    course = Course("math-101", "Algebra I", "teacher@example.edu")
    deadlines = [LearnerDeadline("learner-7", "math-101", now + timedelta(days=1))]
    client = InfraiClient()
    client.create_queue("edtech-deadline-reminders")
    count = publish_due_reminders(client, "edtech-deadline-reminders", course, deadlines, now)
    print(f"published {count} deadline reminder(s)")


if __name__ == "__main__":
    main()
