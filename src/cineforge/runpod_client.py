"""Minimal RunPod Serverless REST API client.

Talks to ``https://api.runpod.ai/v2/{endpoint_id}`` using the documented
``/run`` (async submit) and ``/status/{job_id}`` (poll / fetch result) routes.
Credentials come from the environment (see ``.env.example``).
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

API_BASE = "https://api.runpod.ai/v2"

# Terminal statuses from RunPod Serverless job lifecycle.
TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"})


class RunPodConfigError(RuntimeError):
    """Raised when required RunPod environment configuration is missing."""


class RunPodAPIError(RuntimeError):
    """Raised when the RunPod API returns an unexpected or error response."""


def load_config(
    *,
    api_key: str | None = None,
    endpoint_id: str | None = None,
    dotenv_path: str | None = None,
) -> tuple[str, str]:
    """Load ``RUNPOD_API_KEY`` and ``RUNPOD_ENDPOINT_ID`` from env / ``.env``.

    Explicit kwargs override environment values. Raises ``RunPodConfigError``
    with a clear message if either value is missing.
    """
    load_dotenv(dotenv_path)

    key = api_key if api_key is not None else os.getenv("RUNPOD_API_KEY", "").strip()
    endpoint = (
        endpoint_id
        if endpoint_id is not None
        else os.getenv("RUNPOD_ENDPOINT_ID", "").strip()
    )

    missing: list[str] = []
    if not key:
        missing.append("RUNPOD_API_KEY")
    if not endpoint:
        missing.append("RUNPOD_ENDPOINT_ID")
    if missing:
        raise RunPodConfigError(
            "Missing required RunPod configuration: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and set the values, "
            "or export them in your shell."
        )
    return key, endpoint


class RunPodClient:
    """Thin wrapper around RunPod Serverless REST endpoints."""

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        *,
        session: requests.Session | None = None,
        base_url: str = API_BASE,
    ) -> None:
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()

    @classmethod
    def from_env(cls, **kwargs: Any) -> RunPodClient:
        """Construct a client from environment / ``.env`` configuration."""
        api_key, endpoint_id = load_config()
        return cls(api_key, endpoint_id, **kwargs)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _endpoint_url(self, *parts: str) -> str:
        return "/".join((self.base_url, self.endpoint_id, *parts))

    def submit_job(
        self,
        prompt: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Submit an async job via ``POST /v2/{endpoint_id}/run``.

        The body follows RunPod's documented shape::

            {"input": {"prompt": "...", ...optional params}}

        Returns the JSON response (expects at least an ``id`` job id).
        """
        payload: dict[str, Any] = {"input": {"prompt": prompt}}
        if params:
            payload["input"].update(params)

        response = self.session.post(
            self._endpoint_url("run"),
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        return self._parse_response(response, expect_job_id=True)

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Poll job status via ``GET /v2/{endpoint_id}/status/{job_id}``."""
        response = self.session.get(
            self._endpoint_url("status", job_id),
            headers=self._headers(),
            timeout=60,
        )
        return self._parse_response(response)

    def fetch_result(
        self,
        job_id: str,
        *,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
    ) -> dict[str, Any]:
        """Poll until the job reaches a terminal status, then return the payload.

        On ``COMPLETED``, the response typically includes an ``output`` field
        (URLs, base64, or structured worker output depending on the endpoint).
        Raises ``RunPodAPIError`` on failure / cancel / timeout statuses, or if
        polling exceeds ``timeout`` seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            status_payload = self.get_job_status(job_id)
            status = str(status_payload.get("status", "")).upper()

            if status == "COMPLETED":
                return status_payload
            if status in TERMINAL_STATUSES:
                raise RunPodAPIError(
                    f"RunPod job {job_id} ended with status {status}: "
                    f"{status_payload.get('error') or status_payload}"
                )
            if time.monotonic() >= deadline:
                raise RunPodAPIError(
                    f"Timed out after {timeout}s waiting for RunPod job {job_id} "
                    f"(last status: {status or 'unknown'})"
                )
            time.sleep(poll_interval)

    @staticmethod
    def _parse_response(
        response: requests.Response,
        *,
        expect_job_id: bool = False,
    ) -> dict[str, Any]:
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:500] if response.text else str(exc)
            raise RunPodAPIError(
                f"RunPod API HTTP {response.status_code}: {detail}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RunPodAPIError(
                "RunPod API returned non-JSON response"
            ) from exc

        if not isinstance(data, dict):
            raise RunPodAPIError(f"Unexpected RunPod response type: {type(data)}")

        if expect_job_id and not data.get("id"):
            raise RunPodAPIError(
                f"RunPod /run response missing job id: {data}"
            )
        return data


def generate(
    prompt: str,
    *,
    params: dict[str, Any] | None = None,
    poll_interval: float = 2.0,
    timeout: float = 600.0,
    client: RunPodClient | None = None,
) -> dict[str, Any]:
    """High-level helper: submit a prompt job, poll, and return the result."""
    rp = client or RunPodClient.from_env()
    submitted = rp.submit_job(prompt, params=params)
    job_id = str(submitted["id"])
    return rp.fetch_result(job_id, poll_interval=poll_interval, timeout=timeout)
