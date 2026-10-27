from datetime import datetime, timedelta, timezone

from reminder_scheduler import Course, LearnerDeadline, reminder_payload


def test_deadline_inside_two_day_window_produces_educator_report_payload():
    now = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
    course = Course("course-1", "Physics", "educator@example.edu")
    deadline = LearnerDeadline("learner-1", "course-1", now + timedelta(days=1))

    result = reminder_payload(course, deadline, now)

    assert result == {
        "learner_id": "learner-1",
        "course_id": "course-1",
        "course_title": "Physics",
        "deadline": "2026-10-24T09:00:00+00:00",
        "educator_email": "educator@example.edu",
    }


def test_deadline_outside_window_is_not_published():
    now = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
    course = Course("course-1", "Physics", "educator@example.edu")
    deadline = LearnerDeadline("learner-1", "course-1", now + timedelta(days=3))

    assert reminder_payload(course, deadline, now) is None
