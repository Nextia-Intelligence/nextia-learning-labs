"""The inspector's copies of the project's code and data are byte-identical to the project's files.

The project folder: INSPECTOR_PROJECT, ../project (beside the inspector) or ../snapshots/end-of-m08 (the labs
layout). Without it (for example a download of the inspector alone) the test is skipped.
"""

import pytest

import sync


@pytest.fixture(scope="module")
def project():
    p = sync.find_project()
    if p is None:
        pytest.skip("the course project is not beside the inspector (set INSPECTOR_PROJECT)")
    return p


def test_vendored_code_is_identical(project):
    assert [d for d in sync.differences(project) if "vendor/" in d] == [], "run: python sync.py"


def test_built_in_data_is_identical(project):
    assert sync.differences(project) == [], "run: python sync.py"


def test_vendored_files_are_listed():
    for dst in sync.CODE.values():
        assert (sync.PACKAGE / dst).exists(), dst
