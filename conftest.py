import importlib
import re
import time
import typing
from pathlib import Path

import pytest
from mypy import api

code_rxp = re.compile('```python(.*?)```', re.DOTALL | re.MULTILINE)


class MyPyValidationError(BaseException):
    """A validation error occurred when MyPy attempted to validate the code"""


def fake_print(*args, **kwargs):
    """Dummy replacement for print() that does nothing"""
    pass


def pytest_collect_file(parent, path):
    """Collect all file suitable for use in tests"""
    if path.basename == "README.md":
        return ReadmeFile.from_parent(parent, path=Path(path))


class ReadmeFile(pytest.File):
    """A Markdown formatted readme file containing code snippets"""

    def collect(self):
        """Collect all code snippets"""
        raw_text = self.fspath.open().read()
        for idx, code in enumerate(code_rxp.findall(raw_text), 1):
            yield ReadmeItem.from_parent(
                self, name=str(idx), spec=code.strip()
            )


def _with_patched_sleep(func, *args, **kwargs):
    """Patch the sleep function so that it does nothing"""
    _sleep = time.sleep
    time.sleep = lambda *args: None
    try:
        return func(*args, **kwargs)
    finally:
        time.sleep = _sleep


class ReadmeItem(pytest.Item):
    """A readme test item that validates a code snippet"""
    builtins = (
        ('typing', typing),
        ('datetime', importlib.import_module('datetime')),
        ('hashlib', importlib.import_module('hashlib')),
        ('print', fake_print)
    )

    def __init__(self, name, parent, spec):
        super().__init__(name, parent)
        self.spec = spec

    def runtest(self):
        """Run the test"""
        builtins = dict(self.builtins)
        byte_code = compile(self.spec, '<inline>', 'exec')
        _with_patched_sleep(exec, byte_code, builtins)
        msg, _, error = api.run(['--no-color-output', '-c', self.spec])
        if error:
            # Ignore missing return statements
            if "Missing return statement" in msg:
                return
            # Ignore missing errors related to the injected names
            for name in builtins:
                if f"Name '{name}' is not defined" in msg:
                    break
            else:
                raise MyPyValidationError(msg)

    def repr_failure(self, excinfo, **kwargs):
        """ called when self.runtest() raises an exception. """
        return (
            f"Code snippet {self.name} raised an error: {excinfo.value}. "
            f"The executed code was: {self.spec}"
        )

    def reportinfo(self):
        """Report some basic information on the test outcome"""
        return self.fspath, 0, "usecase: {}".format(self.name)
