# GitHub Crawler

**NOTE: This is a coding challenge for a job application. So the script is limited and parses only the first page of search results.**

This is a Python script to search GitHub for repositories, issues, or wikis based on specified search parameters. The script is implemented using `argparse`, `json`, `re`, `requests`, `typing`, `enum`, `lxml`, and `pydantic` libraries.

## Installation

To use this script, you need to clone this repository and install the required packages. You can use the following commands to install the required packages:

```
$ git clone https://github.com/htrueman/github-crawler.git
$ cd github-crawler
$ pip install -r requirements.txt
```

## Usage

To use the script, you need to pass the following arguments:

```
--config_path: Path to the search parameters JSON file. Default: "search_params.json"
--results_path: Path to save the search results JSON file. Default: "results.json"
```

You can run the script using the following command:

```
$ python main.py --config_path <path-to-config-file> --results_path <path-to-results-file>
```

## Configuration

You need to provide a configuration file in JSON format, which should contain the following fields:

```
{
    "keywords": ["<keyword-1>", "<keyword-2>", ...],  // List of keywords to search for
    "proxies": ["<proxy-1>", "<proxy-2>", ...],  // List of proxies to use for the search
    "type": "<search-type>"  // Search type: "Repositories", "Issues", or "Wikis"
}
```

You can find a sample configuration file in `config.json.sample`.

## Examples

Here are some examples of how to use the script:

To search for repositories based on the configuration file "n.json" and save the results in "results.json":

```
$ python main.py
```

To search for repositories based on the configuration file "config2.json" and save the results in "results2.json":

```
$ python main.py --config_path config2.json --results_path results2.json
```

## Tests, Code Formatting, and Type Checking
To run the tests, use the following command:
```
$ pytest --cov=main tests/
```
To check the code formatting with Black, use the following command:
```
$ black .
```
To run the type checker with Mypy, use the following command:
```
$ mypy .
```