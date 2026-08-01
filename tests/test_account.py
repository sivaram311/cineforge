"""Unit tests for cineforge.account (mocked HTTP — no live network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from cineforge.account import GRAPHQL_URL, get_account_balance
from cineforge.runpod_client import RunPodAPIError, RunPodConfigError


FAKE_KEY = "fake-test-key"


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


def test_get_account_balance_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RUNPOD_API_KEY", raising=False)
    with patch("cineforge.account.load_dotenv"):
        with pytest.raises(RunPodConfigError, match="RUNPOD_API_KEY"):
            get_account_balance()


def test_get_account_balance_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RUNPOD_API_KEY", FAKE_KEY)
    myself = {
        "id": "user_abc",
        "email": "user@example.com",
        "clientBalance": 12.34,
        "currentSpendPerHr": 0.01,
    }
    mock_post = MagicMock(
        return_value=_mock_response(json_data={"data": {"myself": myself}})
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            result = get_account_balance()

    assert result == myself
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == GRAPHQL_URL
    assert kwargs["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
    assert "myself" in kwargs["json"]["query"]
    assert "clientBalance" in kwargs["json"]["query"]


def test_get_account_balance_explicit_key_overrides_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RUNPOD_API_KEY", "env-key-should-not-be-used")
    myself = {
        "id": "user_xyz",
        "email": "x@example.com",
        "clientBalance": 1.0,
        "currentSpendPerHr": 0.0,
    }
    mock_post = MagicMock(
        return_value=_mock_response(json_data={"data": {"myself": myself}})
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            result = get_account_balance(api_key=FAKE_KEY)

    assert result["clientBalance"] == 1.0
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == (
        f"Bearer {FAKE_KEY}"
    )


def test_get_account_balance_http_error() -> None:
    mock_post = MagicMock(
        return_value=_mock_response(status_code=401, text="unauthorized")
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            with pytest.raises(RunPodAPIError, match="HTTP 401"):
                get_account_balance(api_key=FAKE_KEY)


def test_get_account_balance_graphql_errors() -> None:
    mock_post = MagicMock(
        return_value=_mock_response(
            json_data={"errors": [{"message": "Not authorized"}]}
        )
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            with pytest.raises(RunPodAPIError, match="GraphQL errors"):
                get_account_balance(api_key=FAKE_KEY)


def test_get_account_balance_missing_myself() -> None:
    mock_post = MagicMock(
        return_value=_mock_response(json_data={"data": {"myself": None}})
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            with pytest.raises(RunPodAPIError, match="missing myself"):
                get_account_balance(api_key=FAKE_KEY)


def test_http_error_redacts_api_key() -> None:
    leaky = f"denied for key {FAKE_KEY}"
    mock_post = MagicMock(
        return_value=_mock_response(status_code=403, text=leaky)
    )

    with patch("cineforge.account.load_dotenv"):
        with patch("cineforge.account.requests.post", mock_post):
            with pytest.raises(RunPodAPIError) as exc_info:
                get_account_balance(api_key=FAKE_KEY)

    assert FAKE_KEY not in str(exc_info.value)
    assert "***" in str(exc_info.value)
