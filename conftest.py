# content of conftest.py
import datetime
import re
import typing

import pytest

code_rxp = re.compile('```python(.*?)```', re.DOTALL | re.MULTILINE)


class FakeTimeModule:
    def sleep(self, seconds):
        pass


def fake_print(*args, **kwargs):
    pass


def pytest_collect_file(parent, path):
    if path.basename == "README.md":
        return ReadmeFile.from_parent(parent, fspath=path)


class ReadmeFile(pytest.File):
    def collect(self):
        raw = self.fspath.open().read()
        for idx, code in enumerate(code_rxp.findall(raw), 1):
            yield ReadmeItem.from_parent(
                self, name=str(idx), spec=code.strip()
            )


class ReadmeItem(pytest.Item):
    def __init__(self, name, parent, spec):
        super().__init__(name, parent)
        self.spec = spec

    def runtest(self):
        builtins = {
            'typing': typing,
            'time': FakeTimeModule(),
            'datetime': datetime,
            'print': fake_print
        }
        byte_code = compile(self.spec, '<inline>', 'exec')
        exec(byte_code, builtins)

    def repr_failure(self, excinfo, **kwargs):
        """ called when self.runtest() raises an exception. """
        return (
            f"Code snippet {self.name} raised an error: {excinfo.value}. "
            f"The executed code was: {self.spec}"
        )

    def reportinfo(self):
        return self.fspath, 0, "usecase: {}".format(self.name)
