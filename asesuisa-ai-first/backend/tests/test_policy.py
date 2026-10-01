import json

import pytest

from app.ai.artifact_generators import derive_acceptance, derive_api_contract
from app.pipeline import codegen, policy, testgen
from tests.helpers import GOOD


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess",
        "import socket",
        "from os import system",
        "import os\nos.system('x')",
        "import os\nos.popen('x')",
        "eval('1')",
        "exec('x')",
        "open('/etc/passwd')",
        "__import__('os')",
        "x = ().__class__.__bases__",
        "from . import secreto",
        "import requests",
        "from shutil import rmtree",
        "def f(:",
    ],
)
def test_malicious_or_invalid_source_is_rejected(source: str) -> None:
    assert policy.check_source("x.py", source), source


def test_environ_is_the_only_allowed_os_access() -> None:
    assert not policy.check_source("x.py", "from os import environ\nx = environ.get('A')")
    assert not policy.check_source("x.py", "import os\nx = os.environ.get('A')")


def test_generated_code_and_tests_pass_policy() -> None:
    payload = json.dumps(
        {
            "openapi": derive_api_contract(GOOD).openapi,
            "criteria": [c.model_dump() for c in derive_acceptance(GOOD).criteria],
        }
    )
    files = {**codegen.generate(payload).files, **testgen.generate(payload).files}
    assert policy.check_files(files) == []


def test_non_python_files_are_ignored_by_policy() -> None:
    assert policy.check_files({"requirements.txt": "import subprocess"}) == []
