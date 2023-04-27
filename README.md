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

### Sample Results Output
```
[
    {
        "url": "https://github.com/atuldjadhav/DropBox-Cloud-Storage",
        "extra": {
            "owner": "atuldjadhav",
            "language_stats": {
                "CSS": 52.0,
                "JavaScript": 47.2,
                "HTML": 0.8
            }
        }
    },
    {
        "url": "https://github.com/michealbalogun/Horizon-dashboard",
        "extra": {
            "owner": "michealbalogun",
            "language_stats": {
                "Python": 100.0
            }
        }
    }
]
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

## Ideas and Thoughts of Improvements

1. Add support for pagination: Currently, the script only processes the first page of search results. Adding support for pagination would allow the script to retrieve and process more search results.

1. Implement a retry mechanism: Sometimes requests may fail due to various reasons such as network issues, server errors, or rate limits. Implementing a retry mechanism would enable the script to retry the failed requests automatically.

1. Add support for multiple search types: Currently, the script only supports repositories, issues, and wikis. Adding support for other search types such as users, organizations, and topics would increase the script's flexibility.

1. Implement caching: Caching the search results and language statistics for a certain period of time could improve the script's performance and reduce the number of requests sent to GitHub.

1. Add support for multiple search engines: Currently, the script only uses GitHub for searching. Adding support for other search engines such as GitLab, Bitbucket, and SourceForge would enable the script to retrieve search results from different sources.

1. Improve error handling: The script could be improved by adding more detailed error messages and handling different types of errors more gracefully.

1. Add support for more search parameters: Currently, the script only supports keywords and proxies. Adding support for other search parameters such as filters, language, and date range would increase the script's versatility.

1. Implement multithreading: The script could be improved by implementing multithreading to process multiple search results simultaneously, which could significantly reduce the execution time.