import pytest

from breakbot.ingestion import parse_github_url


def test_parse_github_url_accepts_owner_repo():
    repo = parse_github_url("https://github.com/example/project")

    assert repo.owner == "example"
    assert repo.name == "project"


def test_parse_github_url_rejects_non_github():
    with pytest.raises(ValueError):
        parse_github_url("https://example.com/example/project")
