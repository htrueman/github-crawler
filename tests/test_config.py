import json
import os
import tempfile
import pytest
from main import SearchParams, SearchType, read_config


def test_read_config():
    search_params = {
        "keywords": ["test"],
        "proxies": ["http://proxy.com"],
        "type": SearchType.REPOSITORIES,
    }
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(search_params, f)
        temp_config_path = f.name

    search_params_obj = read_config(temp_config_path)

    assert isinstance(search_params_obj, SearchParams)
    assert search_params_obj.keywords == search_params["keywords"]
    assert search_params_obj.proxies == search_params["proxies"]
    assert search_params_obj.type == search_params["type"]

    f.close()
    os.unlink(f.name)


def test_read_config_invalid():
    search_params = {"keywords": ["test"]}
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump(search_params, f)
        temp_config_path = f.name

    with pytest.raises(ValueError):
        read_config(temp_config_path)

    f.close()
    os.unlink(f.name)
