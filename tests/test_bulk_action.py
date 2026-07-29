"""Tests for bulk action result helpers."""

from repomanager.ui.confirm_dialog import DELETE_CONFIRM_WORD
from repomanager.workers.api_worker import ActionFailure, BulkActionResult


def test_bulk_action_result_counts() -> None:
    result = BulkActionResult(
        action="delete",
        succeeded=["a/b", "c/d"],
        failed=[ActionFailure("e/f", "boom")],
    )
    assert result.success_count == 2
    assert result.failure_count == 1


def test_delete_confirm_word() -> None:
    assert DELETE_CONFIRM_WORD == "DELETE"
