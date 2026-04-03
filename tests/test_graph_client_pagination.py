"""Tests for OData pagination helper."""

from m365_posture.graph_client import get_all_odata_pages


def test_get_all_odata_pages_follows_next_link_variants() -> None:
    calls: list = []

    def fetch_page(next_url: str | None):
        calls.append(next_url)
        if next_url is None:
            return {"value": [1], "odata.nextLink": "https://graph.example/p2"}
        return {"value": [2]}

    merged = get_all_odata_pages(fetch_page)
    assert merged == [1, 2]
    assert calls == [None, "https://graph.example/p2"]
