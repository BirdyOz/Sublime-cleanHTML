"""Headless CleanHTML regression suite using narrow Sublime API stubs."""

import importlib.util
from pathlib import Path
import re
import sys
import types
import unittest

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.clean_html_cases import FUNCTION_CASES, STRUCTURE_CASES  # noqa: E402


class Settings:
    def get(self, _key, default=None):
        return default


def load_plugin_module():
    sublime = types.ModuleType("sublime")
    sublime.load_settings = lambda _name: Settings()
    sublime.set_timeout = lambda callback, _timeout=0: callback()
    sublime.status_message = lambda _message: None

    sublime_plugin = types.ModuleType("sublime_plugin")
    sublime_plugin.TextCommand = object

    sys.modules["sublime"] = sublime
    sys.modules["sublime_plugin"] = sublime_plugin

    plugin_path = PROJECT_ROOT / "GB-clean-HTML.py"
    spec = importlib.util.spec_from_file_location("clean_html_plugin", plugin_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = load_plugin_module()


def canonical_html(value):
    return str(BeautifulSoup(value, "html.parser"))


class CleanHtmlTests(unittest.TestCase):
    def test_tinymce_command_pipeline_all_modes(self):
        class Selection(list):
            pass

        class View:
            def __init__(self, value):
                self.value = value
                self.selection = Selection([0])

            def run_command(self, name):
                if name == "select_all":
                    self.selection[:] = [0]
                elif name == "join_lines":
                    self.value = " ".join(self.value.splitlines())
                else:
                    raise AssertionError("Unexpected command: " + name)

            def sel(self):
                return self.selection

            def substr(self, _region):
                return self.value

            def replace(self, _edit, _region, value):
                self.value = value

            def set_status(self, _key, _value):
                pass

            def erase_status(self, _key):
                pass

        source = '<div></div><span class="icon"></span><i aria-hidden="true">&nbsp;</i><p data-mce-style="left">Text</p><img src="real.jpg" data-mce-src=\'draft.jpg\'><p>&nbsp;</p>'
        for mode in sorted(MODULE.VALID_CLEANHTML_TYPES):
            with self.subTest(mode=mode):
                command = MODULE.CleanHtml()
                command.view = View(source)
                command.run(None, type=mode, no_prettify=True)
                soup = BeautifulSoup(command.view.value, "html.parser")
                for name in ("div", "span", "i"):
                    self.assertEqual(soup.find(name).get_text(), "\xa0")
                self.assertEqual(soup.img["src"], "real.jpg")
                self.assertEqual(len(soup.find_all("p")), 1)
                self.assertFalse(any(name.startswith("data-mce-") for tag in soup.find_all(True) for name in tag.attrs))
                first = canonical_html(command.view.value)
                command.run(None, type=mode, no_prettify=True)
                self.assertEqual(canonical_html(command.view.value), first)


def make_function_test(case):
    def test(self):
        function = getattr(MODULE, case["function"])
        self.assertEqual(
            canonical_html(function(case["input"])), canonical_html(case["expected"])
        )

    return test


def make_structure_test(case):
    def test(self):
        result, removed = MODULE.clean_html_structure(
            case["input"], case["mode"], case["config"]
        )
        self.assertEqual(canonical_html(result), canonical_html(case["expected"]))
        self.assertEqual(removed, case["removed"])

    return test


def install_cases(cases, prefix, factory):
    for index, case in enumerate(cases, start=1):
        slug = re.sub(r"[^a-z0-9]+", "_", case["name"].lower()).strip("_")
        setattr(CleanHtmlTests, f"test_{prefix}_{index:02d}_{slug}", factory(case))


install_cases(FUNCTION_CASES, "function", make_function_test)
install_cases(STRUCTURE_CASES, "structure", make_structure_test)


if __name__ == "__main__":
    unittest.main(verbosity=2)
