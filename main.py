import argparse
import json
import re
import requests
from typing import cast
from enum import Enum
from lxml import html
from random import choice as random_choice
from pydantic import BaseModel, validator
from urllib.parse import urlparse


DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_RESULTS_PATH = "results.json"


class InvalidResponseStatusError(Exception):
    def __init__(self, status_code, message="Request failed with status code"):
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
    def validate_proxies(cls, proxies):
        for proxy in proxies:
            if not re.match(r"^(https?://)?(\w+:?\w*@)?([^\s/:]+)(:\d+)?", proxy):
                raise ValueError("Invalid proxy format")
        return proxies


class GitHubCrawler:
    def __init__(self) -> None:
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

        self.config_path = args.config_path
        self.results_path = args.results_path

    def run(self):
        search_params = self.read_search_params(self.config_path)
        search_url = self.compose_search_url(search_params)
        proxy = self.get_random_proxy(search_params.proxies)
        search_page_html = self.retrieve_search_page_html(search_url, proxy)
        results = self.parse_search_results(search_page_html)
        self.write_results(results, self.results_path)

    @staticmethod
    def read_search_params(search_params_file: str) -> SearchParams:
        with open(search_params_file, "r") as f:
            search_params_json = json.load(f)
        return SearchParams(**search_params_json)

    @staticmethod
    def get_is_issue_filter(search_type: SearchType) -> str:
        """Add is:issue filter to search query to exclude pull requests from results
        as they are treated as issue types by GitHub.
        """

        if search_type == SearchType.ISSUES:
            return "is:issue"
        return ""

    def compose_search_url(self, search_params: SearchParams) -> str:
        base_url = "https://github.com/search"
        type_filter = self.get_is_issue_filter(search_params.type)
        keywords = f"{type_filter}+".join(search_params.keywords)
        url = f"{base_url}?q={keywords}&type={search_params.type}"
        return url

    @staticmethod
    def retrieve_search_page_html(url: str, proxy: dict) -> str:
        r = requests.get(url, proxies=proxy)
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
        result_links = cast(
            list[str],
            root.xpath(
                "//div[contains(@class, 'text-normal')]/descendant::a[starts-with(@href, '/')][1]/@href"
            ),
        )
        for link in result_links:
            repo_url = f"https://github.com{link}"
            results.append({"url": repo_url})
        return results

    @staticmethod
    def write_results(results: list[dict], results_file: str) -> None:
        with open(results_file, "w+") as f:
            json.dump(results, f, indent=4)


if __name__ == "__main__":
    crawler = GitHubCrawler()
    crawler.run()
