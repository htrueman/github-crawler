import json
import tempfile
from unittest import mock
from urllib.parse import urlparse
from pydantic import ValidationError
from pytest import fixture
import pytest
from main import (
    GitHubCrawler,
    InvalidResponseStatusError,
    SearchParams,
    SearchType,
    read_config,
)


@fixture
def search_params():
    with tempfile.NamedTemporaryFile(mode="w") as f:
        f.write(
            json.dumps(
                {
                    "keywords": ["test"],
                    "proxies": ["fake_proxy:8000"],
                    "type": SearchType.ISSUES,
                }
            )
        )
        f.seek(0)
        return read_config(f.name)


@fixture
def crawler(search_params):
    crawler = GitHubCrawler("results.json", search_params)
    return crawler


@fixture
def mock_response():
    with open("tests/fixtures/search_page.html", "r") as f:
        html_string = f.read()
    return html_string


def test_crawler_init(crawler, search_params):
    assert crawler.results_path == "results.json"
    assert crawler.search_params == search_params


def test_read_search_params_success(search_params):
    assert search_params.keywords == ["test"]
    assert search_params.proxies == ["fake_proxy:8000"]
    assert search_params.type == SearchType.ISSUES


def test_read_search_params_fail():
    with pytest.raises(ValidationError):
        SearchParams(keywords=["test"], proxies=["fake_proxy:8000"], type="Wrong")


@pytest.mark.parametrize(
    "search_type, expected_filter",
    [
        (SearchType.REPOSITORIES, ""),
        (SearchType.ISSUES, "is:issue"),
        (SearchType.WIKIS, ""),
    ],
)
def test_get_is_issue_filter(search_type, expected_filter):
    assert GitHubCrawler.get_is_issue_filter(search_type) == expected_filter


@mock.patch("requests.Session.get")
def test_retrieve_search_page_html_success(mock_get, crawler):
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>test</body></html>"
    mock_get.return_value = mock_response

    url = "http://example.com"
    params = {"q": "test", "page": 1, "type": "Issues"}

    result = crawler.retrieve_search_page_html(url, params)

    assert result == "<html><body>test</body></html>"
    mock_get.assert_called_once_with(url, params=params)


@mock.patch("requests.Session.get")
def test_retrieve_search_page_html_failure(mock_get, crawler):
    mock_response = mock.MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    url = "http://example.com"
    params = {"q": "test", "page": 1, "type": "Issues"}

    with pytest.raises(InvalidResponseStatusError):
        crawler.retrieve_search_page_html(url, params)

    mock_get.assert_called_once_with(url, params=params)


def test_get_random_proxy():
    proxies = ["http://1.1.1.1:8080", "https://2.2.2.2:8081"]
    proxy_dict = GitHubCrawler.get_random_proxy(proxies)
    parsed_proxy = urlparse(list(proxy_dict.values())[0])
    sheme = (
        parsed_proxy.scheme.decode()
        if isinstance(parsed_proxy.scheme, bytes)
        else parsed_proxy.scheme
    )

    assert str(parsed_proxy.scheme) == sheme
    assert (
        parsed_proxy.netloc == "2.2.2.2:8081" or parsed_proxy.netloc == "1.1.1.1:8080"
    )


def test_parse_search_results():
    with open("tests/fixtures/search_page.html", "r") as f:
        html_page = f.read()

    results = GitHubCrawler.parse_search_results(html_page)

    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert all("url" in result for result in results)
    assert results[0]["url"] == "https://github.com/atuldjadhav/DropBox-Cloud-Storage"
    assert results[1]["url"] == "https://github.com/michealbalogun/Horizon-dashboard"


@mock.patch("requests.Session.get")
def test_run(mock_get, mock_response, search_params):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_response

    crawler = GitHubCrawler("results.json", search_params)
    results = crawler.run()

    assert len(results) == 2
    assert results[0]["url"] == "https://github.com/atuldjadhav/DropBox-Cloud-Storage"
    assert results[1]["url"] == "https://github.com/michealbalogun/Horizon-dashboard"


def test_parse_repo_page():
    with open("tests/fixtures/repo_page.html", "r") as f:
        html_page = f.read()

    results = GitHubCrawler.parse_repo_page(html_page)

    assert isinstance(results, dict)
    assert results == {"CSS": 52.0, "HTML": 0.8, "JavaScript": 47.2}


def test_update_results(crawler):
    results = [
        {"url": "https://github.com/user1/repo1"},
        {"url": "https://github.com/user2/repo2"},
    ]
    expected_results = [
        {
            "url": "https://github.com/user1/repo1",
            "extra": {
                "owner": "user1",
                "language_stats": {"Python": "80%", "HTML": "20%"},
            },
        },
        {
            "url": "https://github.com/user2/repo2",
            "extra": {
                "owner": "user2",
                "language_stats": {"Python": "80%", "HTML": "20%"},
            },
        },
    ]

    mock_session = mock.MagicMock()
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>...</html>"
    mock_session.get.return_value = mock_response

    crawler.parse_repo_page = mock.MagicMock(
        return_value={"Python": "80%", "HTML": "20%"}
    )
    crawler.session = mock_session
    actual_results = crawler.update_results(results)

    assert actual_results == expected_results
