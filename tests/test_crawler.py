import argparse
import json
import tempfile
from unittest import mock
from urllib.parse import urlparse
from pydantic import ValidationError
from pytest import fixture
import pytest
from main import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_RESULTS_PATH,
    GitHubCrawler,
    InvalidResponseStatusError,
    SearchParams,
    SearchType,
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
        return GitHubCrawler.read_search_params(f.name)


@fixture
def crawler():
    crawler = GitHubCrawler()
    return crawler


@pytest.fixture
def mock_response():
    with open("tests/fixtures/search_page.html", "r") as f:
        html_string = f.read()
    return html_string


def test_crawler_init(crawler):
    assert crawler.config_path == DEFAULT_CONFIG_PATH
    assert crawler.results_path == DEFAULT_RESULTS_PATH


def test_crawler_init_command_line_args():
    with mock.patch(
        "argparse.ArgumentParser.parse_known_args",
        return_value=(
            argparse.Namespace(
                config_path="test_config.json", results_path="test_results.json"
            ),
            [],
        ),
    ):
        crawler = GitHubCrawler()
        assert crawler.config_path == "test_config.json"
        assert crawler.results_path == "test_results.json"


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


@mock.patch("requests.get")
def test_retrieve_search_page_html_success(mock_get):
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>test</body></html>"
    mock_get.return_value = mock_response

    url = "http://example.com"
    proxy = {}

    result = GitHubCrawler.retrieve_search_page_html(url, proxy)

    assert result == "<html><body>test</body></html>"
    mock_get.assert_called_once_with(url, proxies=proxy)


@mock.patch("requests.get")
def test_retrieve_search_page_html_failure(mock_get):
    mock_response = mock.MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    url = "http://example.com"
    proxy = {}

    with pytest.raises(InvalidResponseStatusError):
        GitHubCrawler.retrieve_search_page_html(url, proxy)

    mock_get.assert_called_once_with(url, proxies=proxy)


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


def test_write_results(tmpdir):
    results_file = tmpdir.join("results.json")

    # call the method with some sample results and the temporary file path
    sample_results = [{"url": "https://github.com/testuser/testrepo"}]
    GitHubCrawler.write_results(sample_results, str(results_file))

    # verify that the file was created and contains the expected data
    assert results_file.exists()
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == sample_results

    # call the method again with a different set of results and verify the file contents are updated
    updated_results = [{"url": "https://github.com/anotheruser/anotherrepo"}]
    GitHubCrawler.write_results(updated_results, str(results_file))
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == updated_results

    # call the method with an empty list of results and verify that the file is created but empty
    empty_results = []
    GitHubCrawler.write_results(empty_results, str(results_file))
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == empty_results


@mock.patch("requests.get")
def test_run(mock_get, mock_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = mock_response

    crawler = GitHubCrawler()
    crawler.run()

    # Assert that the expected output file was created
    with open(crawler.results_path, "r") as f:
        results = json.load(f)
    assert len(results) == 2
    assert results[0]["url"] == "https://github.com/atuldjadhav/DropBox-Cloud-Storage"
    assert results[1]["url"] == "https://github.com/michealbalogun/Horizon-dashboard"
