"""Unit tests for cineforge.runpod_client (mocked HTTP — no live network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from cineforge.runpod_client import (
    RunPodAPIError,
    RunPodClient,
    RunPodConfigError,
    generate,
    load_config,
)


FAKE_KEY = "fake-test-key"
FAKE_ENDPOINT = "fake-endpoint-id"


def _mock_response(
    *,
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> MagicMock:
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.text = text or ("" if json_data is None else str(json_data))
    response.json.return_value = json_data if json_data is not None else {}

    def raise_for_status() -> None:
        if status_code >= 400:
            raise requests.HTTPError(f"{status_code} error", response=response)

    response.raise_for_status.side_effect = raise_for_status
    return response


@pytest.fixture
def client() -> RunPodClient:
    session = MagicMock(spec=requests.Session)
    return RunPodClient(FAKE_KEY, FAKE_ENDPOINT, session=session)


def test_load_config_missing_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    monkeypatch.delenv("RUNPOD_ENDPOINT_ID", raising=False)
    with patch("cineforge.runpod_client.load_dotenv"):
        with pytest.raises(RunPodConfigError) as exc_info:
            load_config()
    assert "RUNPOD_API_KEY" in str(exc_info.value)
    assert "RUNPOD_ENDPOINT_ID" in str(exc_info.value)


def test_load_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNPOD_API_KEY", FAKE_KEY)
    monkeypatch.setenv("RUNPOD_ENDPOINT_ID", FAKE_ENDPOINT)
    with patch("cineforge.runpod_client.load_dotenv"):
        key, endpoint = load_config()
    assert key == FAKE_KEY
    assert endpoint == FAKE_ENDPOINT


def test_submit_job_posts_correct_shape(client: RunPodClient) -> None:
    client.session.post.return_value = _mock_response(
        json_data={"id": "job-123", "status": "IN_QUEUE"}
    )

    result = client.submit_job("a cinematic establishing shot", params={"width": 1280})

    assert result["id"] == "job-123"
    client.session.post.assert_called_once()
    args, kwargs = client.session.post.call_args
    assert args[0] == f"https://api.runpod.ai/v2/{FAKE_ENDPOINT}/run"
    assert kwargs["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
    assert kwargs["json"] == {
        "input": {"prompt": "a cinematic establishing shot", "width": 1280}
    }


def test_submit_job_missing_id_raises(client: RunPodClient) -> None:
    client.session.post.return_value = _mock_response(json_data={"status": "IN_QUEUE"})
    with pytest.raises(RunPodAPIError, match="missing job id"):
        client.submit_job("prompt")


def test_get_job_status(client: RunPodClient) -> None:
    client.session.get.return_value = _mock_response(
        json_data={"id": "job-123", "status": "IN_PROGRESS"}
    )

    result = client.get_job_status("job-123")

    assert result["status"] == "IN_PROGRESS"
    args, kwargs = client.session.get.call_args
    assert args[0] == f"https://api.runpod.ai/v2/{FAKE_ENDPOINT}/status/job-123"
    assert kwargs["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"


def test_fetch_result_completed(client: RunPodClient) -> None:
    client.session.get.side_effect = [
        _mock_response(json_data={"id": "job-123", "status": "IN_PROGRESS"}),
        _mock_response(
            json_data={
                "id": "job-123",
                "status": "COMPLETED",
                "output": {"video_url": "https://example.invalid/out.mp4"},
            }
        ),
    ]

    with patch("cineforge.runpod_client.time.sleep"):
        result = client.fetch_result("job-123", poll_interval=0.01, timeout=5.0)

    assert result["status"] == "COMPLETED"
    assert result["output"]["video_url"] == "https://example.invalid/out.mp4"
    assert client.session.get.call_count == 2


def test_fetch_result_failed_raises(client: RunPodClient) -> None:
    client.session.get.return_value = _mock_response(
        json_data={"id": "job-123", "status": "FAILED", "error": "worker boom"}
    )

    with pytest.raises(RunPodAPIError, match="FAILED"):
        client.fetch_result("job-123", poll_interval=0.01, timeout=5.0)


def test_generate_end_to_end(client: RunPodClient) -> None:
    client.session.post.return_value = _mock_response(
        json_data={"id": "job-abc", "status": "IN_QUEUE"}
    )
    client.session.get.return_value = _mock_response(
        json_data={
            "id": "job-abc",
            "status": "COMPLETED",
            "output": {"ok": True},
        }
    )

    with patch("cineforge.runpod_client.time.sleep"):
        result = generate("hello world", client=client, poll_interval=0.01)

    assert result["output"] == {"ok": True}


def test_http_error_surfaces_as_api_error(client: RunPodClient) -> None:
    client.session.post.return_value = _mock_response(
        status_code=401, text="unauthorized", json_data={"error": "unauthorized"}
    )
    with pytest.raises(RunPodAPIError, match="HTTP 401"):
        client.submit_job("prompt")
