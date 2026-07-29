"""GitHub Models / Copilot-assisted description suggestions."""

from __future__ import annotations

import requests

from repomanager.services.github_client import GitHubClientError

MODELS_CATALOG_URL = "https://models.github.ai/catalog/models"
MODELS_CHAT_URL = "https://models.github.ai/inference/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"


class CopilotAccessError(GitHubClientError):
    """Raised when GitHub Models / Copilot access is unavailable."""


def check_models_access(token: str) -> bool:
    """Return True if the token can access GitHub Models (Copilot-linked)."""
    try:
        response = requests.get(
            MODELS_CATALOG_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=20,
        )
    except requests.RequestException:
        return False
    return response.status_code == 200


def suggest_repository_description(
    token: str,
    *,
    full_name: str,
    current_description: str,
    readme_excerpt: str,
) -> str:
    """Ask GitHub Models to propose a short Korean repository description."""
    if not check_models_access(token):
        raise CopilotAccessError(
            "GitHub Models / Copilot 호출 권한이 없습니다.\n"
            "GitHub Copilot 또는 Models 접근이 가능한 계정/토큰인지 확인하세요.",
            status=403,
        )

    prompt = (
        "당신은 GitHub 저장소 설명을 작성하는 도우미입니다.\n"
        "아래 정보를 보고 한국어로 저장소 description을 한 문장~두 문장으로 작성하세요.\n"
        "350자 이내, 과장 없이, 수업/실습용일 수 있음을 고려하세요.\n"
        "따옴표나 마크다운 없이 설명 본문만 출력하세요.\n\n"
        f"저장소: {full_name}\n"
        f"현재 설명: {current_description or '(없음)'}\n"
        f"README 일부:\n{readme_excerpt or '(README 없음)'}\n"
    )
    try:
        response = requests.post(
            MODELS_CHAT_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={
                "model": DEFAULT_MODEL,
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": "Respond with repository description only."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise GitHubClientError(f"AI 요청 실패: {exc}") from exc

    if response.status_code in {401, 403}:
        raise CopilotAccessError(
            "GitHub Models / Copilot 호출 권한이 없습니다.\n"
            f"HTTP {response.status_code}",
            status=response.status_code,
        )
    if response.status_code >= 400:
        raise GitHubClientError(
            f"AI 추천 실패 (HTTP {response.status_code}): {response.text[:300]}",
            status=response.status_code,
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GitHubClientError("AI 응답 형식을 해석하지 못했습니다.") from exc
    text = str(content).strip().strip('"').strip("'")
    if not text:
        raise GitHubClientError("AI가 빈 설명을 반환했습니다.")
    return text[:350]
