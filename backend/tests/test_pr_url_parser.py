from app.services.pr_url_parser import PRUrlParseError, parse_github_pr_url


def test_parse_github_pr_url_returns_parsed_info_for_valid_url() -> None:
    result = parse_github_pr_url("https://github.com/openai/openai-python/pull/123")

    assert result.owner == "openai"
    assert result.repo == "openai-python"
    assert result.pull_number == 123
    assert result.api_url == "https://api.github.com/repos/openai/openai-python/pulls/123"


def test_parse_github_pr_url_rejects_non_github_host() -> None:
    try:
        parse_github_pr_url("https://example.com/openai/openai-python/pull/123")
    except PRUrlParseError as exc:
        assert "github.com" in str(exc)
    else:
        raise AssertionError("Expected PRUrlParseError for non-GitHub host")


def test_parse_github_pr_url_rejects_empty_value() -> None:
    try:
        parse_github_pr_url("")
    except PRUrlParseError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected PRUrlParseError for empty URL")
