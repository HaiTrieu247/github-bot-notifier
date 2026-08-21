"""Tests for GitHub event parsing."""

from src.github.events import (
    parse_push_event,
    parse_workflow_run_event,
    parse_pull_request_event,
)

PUSH_PAYLOAD = {
    "ref": "refs/heads/main",
    "repository": {"full_name": "Kens0107/homestay-backend", "name": "homestay-backend"},
    "head_commit": {
        "id": "a82f31cdeadbeef",
        "message": "fix authentication bug\n\nDetails here",
        "url": "https://github.com/Kens0107/homestay-backend/commit/a82f31c",
        "author": {"username": "Kens0107", "name": "Ken"},
    },
    "commits": [{}, {}, {}],
    "compare": "https://github.com/Kens0107/homestay-backend/compare/abc...def",
}


def test_parse_push_event():
    event = parse_push_event(PUSH_PAYLOAD)
    assert event.repo_full_name == "Kens0107/homestay-backend"
    assert event.branch == "main"
    assert event.author == "Kens0107"
    assert event.commit_sha == "a82f31c"
    assert event.commit_message == "fix authentication bug"
    assert event.files_changed == 3


WORKFLOW_PAYLOAD = {
    "action": "completed",
    "repository": {"full_name": "Kens0107/homestay-backend", "name": "homestay-backend"},
    "workflow_run": {
        "id": 12345,
        "name": "CI",
        "head_branch": "main",
        "head_sha": "a82f31cdeadbeef",
        "status": "completed",
        "conclusion": "success",
        "html_url": "https://github.com/runs/12345",
        "run_started_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-01T10:02:31Z",
    },
}


def test_parse_workflow_success():
    event = parse_workflow_run_event(WORKFLOW_PAYLOAD)
    assert event.status == "completed"
    assert event.conclusion == "success"
    assert event.workflow_name == "CI"
    assert event.run_id == 12345


PR_PAYLOAD = {
    "action": "opened",
    "repository": {"full_name": "Kens0107/homestay-backend", "name": "homestay-backend"},
    "pull_request": {
        "number": 42,
        "title": "Add authentication middleware",
        "html_url": "https://github.com/pr/42",
        "user": {"login": "Kens0107"},
        "head": {"ref": "feature/auth"},
        "base": {"ref": "main"},
        "merged": False,
        "merged_by": None,
    },
}


def test_parse_pull_request_opened():
    event = parse_pull_request_event(PR_PAYLOAD)
    assert event.action == "opened"
    assert event.pr_number == 42
    assert event.author == "Kens0107"
    assert event.head_branch == "feature/auth"
    assert not event.merged
