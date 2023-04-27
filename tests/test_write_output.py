import json
from main import write_output


def test_write_output(tmpdir):
    results_file = tmpdir.join("results.json")

    # call the method with some sample results and the temporary file path
    sample_results = [{"url": "https://github.com/testuser/testrepo"}]
    write_output(sample_results, str(results_file))

    # verify that the file was created and contains the expected data
    assert results_file.exists()
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == sample_results

    # call the method again with a different set of results and verify the file contents are updated
    updated_results = [{"url": "https://github.com/anotheruser/anotherrepo"}]
    write_output(updated_results, str(results_file))
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == updated_results

    # call the method with an empty list of results and verify that the file is created but empty
    empty_results = []
    write_output(empty_results, str(results_file))
    with open(str(results_file), "r") as f:
        data = json.load(f)
        assert data == empty_results
