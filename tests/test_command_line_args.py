import argparse
import sys
from main import read_command_line_args


def test_read_command_line_args_default():
    args = read_command_line_args()

    assert isinstance(args, argparse.Namespace)
    assert args.config_path == "config.json"
    assert args.results_path == "results.json"


def test_read_command_line_args_custom():
    sys.argv = [
        "test.py",
        "--config_path",
        "custom_config.json",
        "--results_path",
        "custom_results.json",
        "--fake",
        "fake",
    ]

    args = read_command_line_args()

    assert isinstance(args, argparse.Namespace)
    assert args.config_path == "custom_config.json"
    assert args.results_path == "custom_results.json"
    assert not hasattr(args, "fake")
