"""GitHub Models / Copilot-assisted description suggestions."""

from __future__ import annotations

import requests

from repomanager.i18n import get_language, tr
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
    """Ask GitHub Models to propose a short repository description in the UI language."""
    if not check_models_access(token):
        raise CopilotAccessError(tr("ai.no_access"), status=403)

    language = {"ko": "Korean", "en": "English", "ja": "Japanese"}.get(
        get_language(), "English"
    )
    prompt = (
        "You write GitHub repository descriptions.\n"
        f"Based on the info below, write the description in {language}, "
        "one or two sentences, under 350 characters, without exaggeration. "
        "It may be a classroom/practice repository.\n"
        "Output only the description text, no quotes or markdown.\n\n"
        f"Repository: {full_name}\n"
        f"Current description: {current_description or '(none)'}\n"
        f"README excerpt:\n{readme_excerpt or '(no README)'}\n"
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
        raise GitHubClientError(tr("ai.request_failed", exc=exc)) from exc

    if response.status_code in {401, 403}:
        raise CopilotAccessError(
            tr("ai.no_access_http", status=response.status_code),
            status=response.status_code,
        )
    if response.status_code >= 400:
        raise GitHubClientError(
            tr("ai.failed_http", status=response.status_code, body=response.text[:300]),
            status=response.status_code,
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GitHubClientError(tr("ai.bad_response")) from exc
    text = str(content).strip().strip('"').strip("'")
    if not text:
        raise GitHubClientError(tr("ai.empty"))
    return text[:350]
