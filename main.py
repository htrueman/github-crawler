import argparse
import json
import re
import requests
from typing import cast
from enum import Enum
from lxml import html
from random import choice as random_choice
from pydantic import BaseModel, validator
from urllib.parse import urljoin, urlparse


DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_RESULTS_PATH = "results.json"

SEARCH_URL = "https://github.com/search"


class InvalidResponseStatusError(Exception):
    def __init__(
        self, status_code: int, message: str = "Request failed with status code"
    ):
        self.message = f"{message}: {status_code}"
        super().__init__(self.message)


class SearchType(str, Enum):
    REPOSITORIES = "Repositories"
    ISSUES = "Issues"
    WIKIS = "Wikis"


class SearchParams(BaseModel):
    keywords: list[str]
    proxies: list[str]
    type: SearchType

    @validator("proxies")
    def validate_proxies(cls, proxies: list[str]) -> list[str]:
        for proxy in proxies:
            if not re.match(r"^(https?://)?(\w+:?\w*@)?([^\s/:]+)(:\d+)?", proxy):
                raise ValueError("Invalid proxy format")
        return proxies


class GitHubCrawler:
    def __init__(self, results_path: str, search_params: SearchParams) -> None:
        self.results_path = results_path
        self.search_params = search_params
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        self.session.proxies = self.get_random_proxy(self.search_params.proxies)

    def run(self) -> list[dict]:
        search_url, query_params = self.compose_search_query_params(self.search_params)
        search_page_html = self.retrieve_search_page_html(search_url, query_params)
        results = self.parse_search_results(search_page_html)
        if self.search_params.type == SearchType.REPOSITORIES:
            results = self.update_results(results)
        return results

    @staticmethod
    def get_is_issue_filter(search_type: SearchType) -> str:
        """Add is:issue filter to search query to exclude pull requests from results
        as they are treated as issue types by GitHub.
        """

        if search_type == SearchType.ISSUES:
            return "is:issue"
        return ""

    def compose_search_query_params(
        self, search_params: SearchParams
    ) -> tuple[str, dict]:
        type_filter = self.get_is_issue_filter(search_params.type)
        keywords = "+".join([*search_params.keywords, type_filter])
        query_params = {"q": keywords, "type": search_params.type.value}
        return SEARCH_URL, query_params

    def retrieve_search_page_html(self, url: str, params: dict) -> str:
        r = self.session.get(url, params=params)
        if r.status_code != 200:
            raise InvalidResponseStatusError(r.status_code)
        return r.text

    @staticmethod
    def get_random_proxy(proxies: list[str]) -> dict:
        proxy = random_choice(proxies)
        parsed_proxy = urlparse(proxy)
        return {parsed_proxy.scheme or "http": proxy}

    @staticmethod
    def parse_search_results(html_string: str) -> list[dict]:
        results = []
        root = html.fromstring(html_string)
        result_paths = cast(
            list[str],
            root.xpath(
                "//div[contains(@class, 'text-normal')]/descendant::a[starts-with(@href, '/')][1]/@href"
            ),
        )
        for path in result_paths:
            repo_url = urljoin("https://github.com", path)
            results.append({"url": repo_url})
        return results

    @staticmethod
    def parse_repo_page(html_string: str) -> dict:
        results = {}
        root = html.fromstring(html_string)
        language_shares = cast(
            list[str],
            root.xpath(
                "//div[contains(@class, 'BorderGrid')]/descendant::span[contains(@class, 'Progress-item')]/@aria-label"
            ),
        )
        for language_share in language_shares:
            language, share = language_share.split(" ")
            results[language] = round(float(share), 2)
        return results

    def update_results(self, results: list[dict]) -> list[dict]:
        for result in results:
            repo_url = result["url"]
            repo_page_html = self.retrieve_search_page_html(repo_url, {})
            language_stats = self.parse_repo_page(repo_page_html)
            parsed_url = urlparse(repo_url)
            owner = parsed_url.path.split("/")[1]
            result.update({"extra": {"owner": owner, "language_stats": language_stats}})
        return results


def read_command_line_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GitHub crawler script.")
    parser.add_argument(
        "--config_path",
        default=DEFAULT_CONFIG_PATH,
        help="Path to the search parameters JSON file.",
    )
    parser.add_argument(
        "--results_path",
        default=DEFAULT_RESULTS_PATH,
        help="Path to save the search results JSON file.",
    )
    args, _ = parser.parse_known_args()
    return args


def read_config(config_path: str) -> SearchParams:
    with open(config_path, "r") as f:
        search_params_json = json.load(f)
    return SearchParams(**search_params_json)


def write_output(results: list[dict], results_file: str) -> None:
    with open(results_file, "w+") as f:
        json.dump(results, f, indent=4)


def main() -> None:
    command_line_args = read_command_line_args()
    search_params = read_config(command_line_args.config_path)
    crawler = GitHubCrawler(
        results_path=command_line_args.results_path,
        search_params=search_params,
    )
    search_resutls = crawler.run()
    write_output(search_resutls, command_line_args.results_path)


if __name__ == "__main__":
    main()
