from __future__ import annotations

import os
import shutil
import tempfile


TEST_RUNTIME_HOME = tempfile.mkdtemp(prefix="acp-tests-")
os.environ["ACP_RUNTIME_HOME"] = TEST_RUNTIME_HOME


def pytest_sessionfinish(session, exitstatus):  # type: ignore[no-untyped-def]
    shutil.rmtree(TEST_RUNTIME_HOME, ignore_errors=True)

