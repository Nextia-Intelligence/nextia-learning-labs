"""Shared test set-up: the course's documents are made once, in a temporary folder."""

import os

import pytest

from doc_extract import documents, generate


@pytest.fixture(scope="session", autouse=True)
def course_documents(tmp_path_factory):
    """Make the document set (about 10 seconds) and work in a temporary folder, so the tests never
    touch your data/ and out/ folders."""
    root = tmp_path_factory.mktemp("doc-extract")
    data = root / "data"
    generate.write(data)
    old_cwd, old_env = os.getcwd(), os.environ.get("DOCS_DIR")
    os.environ["DOCS_DIR"] = str(data)
    os.chdir(root)
    yield data
    os.chdir(old_cwd)
    if old_env is None:
        os.environ.pop("DOCS_DIR", None)
    else:
        os.environ["DOCS_DIR"] = old_env


@pytest.fixture
def doc():
    """A document of the course's set by ID: doc("D011")."""
    return documents.get
