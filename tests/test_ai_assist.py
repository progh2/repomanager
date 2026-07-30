"""Tests for AI assist access helpers."""

from unittest.mock import MagicMock, patch

import pytest

from repomanager.i18n import set_language, tr
from repomanager.services.ai_assist import CopilotAccessError, suggest_repository_description


@patch("repomanager.services.ai_assist.check_models_access", return_value=False)
def test_suggest_without_access(_check: MagicMock) -> None:
    set_language("ko", notify=False)
    with pytest.raises(CopilotAccessError) as exc:
        suggest_repository_description(
            "token",
            full_name="a/b",
            current_description="",
            readme_excerpt="",
        )
    assert str(exc.value) == tr("ai.no_access")


@patch("repomanager.services.ai_assist.check_models_access", return_value=True)
@patch("repomanager.services.ai_assist.requests.post")
def test_suggest_success(mock_post: MagicMock, _check: MagicMock) -> None:
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "choices": [{"message": {"content": "수업용 데모 저장소입니다."}}]
    }
    text = suggest_repository_description(
        "token",
        full_name="a/b",
        current_description="",
        readme_excerpt="# Hello",
    )
    assert "수업용" in text
