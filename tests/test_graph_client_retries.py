"""Tests for Graph GET retries and :func:`m365_posture.graph_client.sleep_with_backoff`."""

from unittest.mock import MagicMock, patch

from m365_posture.graph_client import execute_graph_get, sleep_with_backoff


@patch("m365_posture.graph_client.time.sleep")
def test_execute_graph_get_retries_429_with_retry_after(mock_sleep: MagicMock) -> None:
    """Retry once after HTTP 429 when ``Retry-After`` is present.

    Args:
        mock_sleep: Patched ``time.sleep`` to assert backoff duration.

    Returns:
        None.
    """
    ok = MagicMock()
    ok.status_code = 200
    ok.json.return_value = {"value": []}

    busy = MagicMock()
    busy.status_code = 429
    busy.headers = {"Retry-After": "1"}

    getter = MagicMock(side_effect=[busy, ok])

    result = execute_graph_get("https://graph.microsoft.com/v1.0/foo", getter)

    assert result == {"value": []}
    assert getter.call_count == 2
    mock_sleep.assert_called_once()
    args, _kwargs = mock_sleep.call_args
    assert args[0] >= 1.0


def test_sleep_with_backoff_respects_retry_after_greater_than_backoff() -> None:
    """Sleep duration is at least ``retry_after_sec`` when it exceeds computed backoff.

    Returns:
        None.
    """
    with patch("m365_posture.graph_client.time.sleep") as mock_sleep:
        sleep_with_backoff(0, retry_after_sec=30.0)
    mock_sleep.assert_called_once()
    slept, = mock_sleep.call_args[0]
    assert slept >= 30.0
