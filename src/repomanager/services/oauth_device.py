"""GitHub OAuth Device Flow helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests

from repomanager.config import ConfigError

DEFAULT_SCOPES = "repo delete_repo read:org"
DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"
VERIFICATION_URL = "https://github.com/login/device"


@dataclass(frozen=True, slots=True)
class DeviceCodeResponse:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


class OAuthError(ConfigError):
    """OAuth / device-flow failure."""


def request_device_code(client_id: str, *, scope: str = DEFAULT_SCOPES) -> DeviceCodeResponse:
    client_id = client_id.strip()
    if not client_id:
        raise OAuthError(
            "OAuth Client ID is empty. Create a GitHub OAuth App and paste the Client ID in Settings."
        )
    response = requests.post(
        DEVICE_CODE_URL,
        headers={"Accept": "application/json"},
        data={"client_id": client_id, "scope": scope},
        timeout=30,
    )
    data = response.json()
    if response.status_code >= 400 or "error" in data:
        message = data.get("error_description") or data.get("error") or response.text
        raise OAuthError(f"Device code request failed: {message}")
    return DeviceCodeResponse(
        device_code=str(data["device_code"]),
        user_code=str(data["user_code"]),
        verification_uri=str(data.get("verification_uri") or VERIFICATION_URL),
        expires_in=int(data.get("expires_in", 900)),
        interval=max(1, int(data.get("interval", 5))),
    )


def poll_for_access_token(
    client_id: str,
    device_code: str,
    *,
    interval: int,
    expires_in: int,
    should_cancel=None,
) -> str:
    """Poll until the user completes browser login. Returns access token."""
    deadline = time.time() + expires_in
    wait = max(1, interval)
    while time.time() < deadline:
        if should_cancel is not None and should_cancel():
            raise OAuthError("Sign-in cancelled.")
        response = requests.post(
            TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=30,
        )
        data = response.json()
        if "access_token" in data:
            token = str(data["access_token"]).strip()
            if not token:
                raise OAuthError("GitHub returned an empty access token.")
            return token

        error = str(data.get("error", ""))
        if error in {"authorization_pending", "slow_down"}:
            if error == "slow_down":
                wait += 5
            time.sleep(wait)
            continue
        if error == "expired_token":
            raise OAuthError("Device code expired. Start sign-in again.")
        if error == "access_denied":
            raise OAuthError("Access denied in the browser.")
        message = data.get("error_description") or error or response.text
        raise OAuthError(f"OAuth failed: {message}")

    raise OAuthError("Timed out waiting for GitHub sign-in.")
