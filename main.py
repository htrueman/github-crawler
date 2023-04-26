import argparse
import json
import requests
from enum import Enum
from lxml import html
from random import choice as random_choice
from dataclasses import dataclass
from urllib.parse import urlparse


class InvalidResponseStatusError(Exception):
    def __init__(self, status_code, message="Request failed with status code"):
        self.message = f"{message}: {status_code}"
        super().__init__(self.message)


class SearchType(str, Enum):
    REPOSITORIES = "Repositories"
    ISSUES = "Issues"
    WIKIS = "Wikis"


@dataclass
class SearchParams:
    keywords: list[str]
    proxies: list[str]
    type: SearchType


def read_search_params(search_params_file: str) -> SearchParams:
    with open(search_params_file, "r") as f:
        search_params_json = json.load(f)
    return SearchParams(**search_params_json)


def get_is_issue_filter(search_type: SearchType) -> str:
    """Add is:issue filter to search query to exclude pull requests from results"""

    if search_type == SearchType.ISSUES:
        return "is:issue"
    return ""


def compose_search_url(search_params: SearchParams) -> str:
    base_url = "https://github.com/search"
    type_filter = get_is_issue_filter(search_params.type)
    keywords = f"{type_filter}+".join(search_params.keywords)
    url = f"{base_url}?q={keywords}&type={search_params.type}"
    return url


def retrieve_search_page_html(url: str, proxy: dict) -> str:
    r = requests.get(url, proxies=proxy)
    if r.status_code != 200:
        raise InvalidResponseStatusError(r.status_code)
    return r.text


def get_random_proxy(proxies: list[str]) -> dict:
    proxy = random_choice(proxies)
    parsed_proxy = urlparse(proxy)
    return {parsed_proxy.scheme: parsed_proxy}


def parse_search_results(html_string: str) -> list[dict]:
    results = []
    root = html.fromstring(html_string)
    repo_links = root.xpath(
        "//div[contains(@class, 'text-normal')]/descendant::a[starts-with(@href, '/')][1]/@href"
    )
    for repo_link in repo_links:
        repo_url = f"https://github.com{repo_link}"
        results.append({"url": repo_url})
    return results


def write_results(results: list[dict], results_file: str) -> None:
    with open(results_file, "w+") as f:
        json.dump(results, f, indent=4)


def main():
    parser = argparse.ArgumentParser(description="GitHub crawler script.")
    parser.add_argument("--config_path", default="search_params.json", help="Path to the search parameters JSON file.")
    parser.add_argument("--results_path", default="results.json", help="Path to save the search results JSON file.")
    args = parser.parse_args()

    config_path = args.config_path
    results_path = args.results_path

    search_params = read_search_params(config_path)
    search_url = compose_search_url(search_params)
    proxy = get_random_proxy(search_params.proxies)
    search_page_html = retrieve_search_page_html(search_url, proxy)
    results = parse_search_results(search_page_html)
    write_results(results, results_path)

if __name__ == "__main__":
    main()
