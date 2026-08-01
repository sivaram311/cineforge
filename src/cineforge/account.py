"""RunPod account / billing helpers (GraphQL).

Separate from ``runpod_client`` (Serverless job submission). Talks to
``https://api.runpod.io/graphql`` for authenticated account balance info.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from cineforge.runpod_client import RunPodAPIError, RunPodConfigError

GRAPHQL_URL = "https://api.runpod.io/graphql"

BALANCE_QUERY = """
query {
  myself {
    id
    email
    clientBalance
    currentSpendPerHr
  }
}
""".strip()


def _redact(text: str, secret: str) -> str:
    """Strip a secret from text so it never appears in error messages."""
    if not secret:
        return text
    return text.replace(secret, "***")


def get_account_balance(api_key: str | None = None) -> dict[str, Any]:
    """Fetch balance / spend for the authenticated RunPod account.

    Reads ``RUNPOD_API_KEY`` from the environment (or ``.env``) when
    ``api_key`` is not passed. Returns the ``myself`` object from GraphQL
    (expects ``id``, ``email``, ``clientBalance``, ``currentSpendPerHr``).

    Raises ``RunPodConfigError`` if the key is missing, ``RunPodAPIError``
    on HTTP / GraphQL / shape failures. Error messages never include the
    raw API key.
    """
    load_dotenv()
    key = api_key if api_key is not None else os.getenv("RUNPOD_API_KEY", "").strip()
    if not key:
        raise RunPodConfigError(
            "Missing required RunPod configuration: RUNPOD_API_KEY. "
            "Copy .env.example to .env and set the value, "
            "or export it in your shell."
        )

    try:
        response = requests.post(
            GRAPHQL_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"query": BALANCE_QUERY},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise RunPodAPIError(
            f"RunPod GraphQL request failed: {_redact(str(exc), key)}"
        ) from exc

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text[:500] if response.text else str(exc)
        raise RunPodAPIError(
            f"RunPod GraphQL HTTP {response.status_code}: {_redact(detail, key)}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RunPodAPIError("RunPod GraphQL returned non-JSON response") from exc

    if not isinstance(payload, dict):
        raise RunPodAPIError(
            f"Unexpected RunPod GraphQL response type: {type(payload)}"
        )

    errors = payload.get("errors")
    if errors:
        raise RunPodAPIError(
            f"RunPod GraphQL errors: {_redact(str(errors), key)}"
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        raise RunPodAPIError(
            f"RunPod GraphQL response missing data: {_redact(str(payload), key)}"
        )

    myself = data.get("myself")
    if not isinstance(myself, dict):
        raise RunPodAPIError(
            f"RunPod GraphQL response missing myself: {_redact(str(payload), key)}"
        )

    return myself
