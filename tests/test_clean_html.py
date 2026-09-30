"""Headless regressions use repository settings and restore all Sublime stubs."""

from copy import deepcopy
import importlib.util
import json
import re
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from tests.clean_html_cases import CASES


def read_raw_settings():
    source = (PROJECT_ROOT / 'CleanHTML.sublime-settings').read_text()
    # Keep quoted strings intact (URLs and regexes can contain comment markers).
    tokens = r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/'
    source = re.sub(tokens, lambda match: match[0] if match[0].startswith('"')
                    else ' ' + '\n' * match[0].count('\n'), source)
    return json.loads(source)


def read_settings():
    return MODULE.expand_rule_groups(read_raw_settings())


class Settings:
    def __init__(self, values):
        self.values = values

    def get(self, key, default=None):
        return self.values.get(key, default)

    def to_dict(self):
        return deepcopy(self.values)


class Region:
    def __init__(self, a, b=None):
        self.a, self.b = a, a if b is None else b


class Selection(list):
    def add(self, region):
        self.append(region)


class View:
    def __init__(self, value):
        self.value = value
        self.selection = Selection([Region(0)])
        self.replacements = 0
        self.commands = []

    def size(self):
        return len(self.value)

    def sel(self):
        return self.selection

    def substr(self, region):
        return self.value[min(region.a, region.b):max(region.a, region.b)]

    def replace(self, edit, region, value):
        self.replacements += 1
        self.value = self.value[:region.a] + value + self.value[region.b:]

    def run_command(self, name):
        self.commands.append(name)
        if name != 'htmlprettify':
            raise AssertionError('Unexpected editor mutation: ' + name)

    def set_status(self, key, value):
        pass

    def erase_status(self, key):
        pass


def load_plugin_module():
    sublime = types.ModuleType('sublime')
    sublime.load_settings = lambda name: Settings(read_raw_settings())
    sublime.Region = Region
    sublime.set_timeout = lambda callback, delay=0: callback()
    sublime.status_message = lambda message: None
    sublime_plugin = types.ModuleType('sublime_plugin')
    sublime_plugin.TextCommand = object
    with patch.dict(sys.modules, {'sublime': sublime, 'sublime_plugin': sublime_plugin}):
        spec = importlib.util.spec_from_file_location('clean_html_plugin', PROJECT_ROOT / 'GB-clean-HTML.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


MODULE = load_plugin_module()


def canonical_html(value):
    return str(BeautifulSoup(value, 'html.parser'))


def config_for_case(case):
    config = read_settings()
    for rule in config['rules']:
        if rule['id'] in case.get('disable', []):
            rule['enabled'] = False
        if rule['id'] in case.get('enable', []):
            rule['enabled'] = True
    config['rules'].extend(deepcopy(case.get('extra_rules', [])))
    if 'protect' in case:
        config['empty_elements']['protect_selectors'] = case['protect']
    return config


class CleanHtmlTests(unittest.TestCase):
    def test_grouped_settings_expand_and_preserve_input(self):
        config = read_raw_settings()
        original = deepcopy(config)
        expanded = MODULE.expand_rule_groups(config)
        self.assertEqual(config, original)
        self.assertIsInstance(expanded['rules'], list)
        self.assertEqual([r['id'] for r in expanded['rules'][:5]],
                         ['editor-overlays', 'readspeaker', 'ghost-message',
                          'bogus-breaks', 'paragraph-only-break'])
        # Object keys may be alphabetized by Sublime; list order must survive.
        reordered = deepcopy(config)
        reordered['rules']['groups'] = dict(sorted(reordered['rules']['groups'].items()))
        self.assertEqual(MODULE.expand_rule_groups(reordered), expanded)

    def test_group_defaults_pairs_and_entry_overrides(self):
        config = read_raw_settings()
        config['rules'] = {'order': ['literal', 'regex'], 'groups': {
            'literal': {'action': 'text', 'defaults': {'selector': '*'}, 'entries': [
                {'label': ['Old', 'New', {'selector': 'p'}]},
                {'disabled': ['New', 'Lost', {'enabled': False}]},
            ]},
            'regex': {'action': 'text', 'defaults': {'selector': 'p'}, 'match': 'regex',
                      'entries': [{'digits': [r'\d+', 'number']}]},
        }}
        output, _ = MODULE.clean_html('<p>Old 123</p><span>Old 123</span>', 'normal', config)
        self.assertEqual(canonical_html(output), '<p>New number</p><span>Old 123</span>')

    def test_invalid_grouped_settings_rejected(self):
        configs = []
        for order in ([], ['remove', 'remove'], ['missing']):
            config = read_raw_settings()
            config['rules']['order'] = order
            configs.append(config)
        for entry in ({'one': 'aside', 'two': 'article'}, {'bad': [1, 2]},
                      {'bad': {'action': 'remove'}}, {'bad': ['x', 'y', {'find': 'z'}]}):
            config = read_raw_settings()
            config['rules']['groups']['remove']['entries'] = [entry]
            configs.append(config)
        duplicate = read_raw_settings()
        duplicate['rules']['groups']['unwrap']['entries'].append({'editor-overlays': 'aside'})
        configs.append(duplicate)
        for config in configs:
            with self.subTest(config=config), self.assertRaises(MODULE.ConfigurationError):
                MODULE.clean_html('<p>Unchanged</p>', 'normal', config)

    def test_shared_cases_and_repeat_run_stability(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                config = config_for_case(case)
                output, counts = MODULE.clean_html(case['source'], case.get('mode', 'normal'), config)
                self.assertEqual(canonical_html(output), canonical_html(case['expected']))
                second, _ = MODULE.clean_html(output, case.get('mode', 'normal'), config)
                self.assertEqual(canonical_html(second), canonical_html(output), 'second run changed content')

    def test_command_pipeline_all_retained_modes(self):
        source = '<div></div><span class="icon"></span><i></i><p data-mce-style="left">Text</p>'
        for mode in read_settings()['modes']:
            with self.subTest(mode=mode):
                command = MODULE.CleanHtml()
                command.view = View(source)
                command.view.selection[:] = [Region(len(source), 5), Region(0)]
                command.run(None, type=mode, no_prettify=True)
                self.assertEqual(command.view.replacements, 1)
                self.assertEqual(command.view.commands, [])
                soup = BeautifulSoup(command.view.value, 'html.parser')
                for name in ('div', 'span', 'i'):
                    self.assertEqual(soup.find(name).get_text(), '\xa0')
                self.assertNotIn('data-mce-style', soup.p.attrs)
                command.run(None, type=mode, no_prettify=True)
                self.assertEqual(command.view.replacements, 1, 'unchanged content was replaced again')
                self.assertEqual(len(command.view.sel()), 2)
                self.assertGreater(command.view.sel()[0].a, command.view.sel()[0].b)

    def test_command_prettify_option(self):
        command = MODULE.CleanHtml()
        command.view = View('<p>Text</p>')
        command.run(None)
        self.assertEqual(command.view.commands, ['htmlprettify'])

    def test_unknown_and_retired_modes_leave_document_untouched(self):
        for mode in ('mp', 'mpextended', 'unknown'):
            command = MODULE.CleanHtml()
            command.view = View('<p data-mce-style="x">Text</p>')
            original = command.view.value
            command.run(None, type=mode)
            self.assertEqual(command.view.value, original)
            self.assertEqual(command.view.replacements, 0)
            self.assertEqual(command.view.commands, [])

    def test_invalid_configs_rejected_atomically(self):
        original = '<pre>First\n    Second</pre>'
        def bad_rule(**values):
            config = read_settings()
            config['rules'][0].update(values)
            return config
        invalid = [
            bad_rule(selector='['), bad_rule(enabled='false'), bad_rule(action='unrecognized'),
            bad_rule(modes=['mp']), bad_rule(typo='x'),
        ]
        config = read_settings()
        config['run_htmlprettify_after_clean'] = 'false'
        invalid.append(config)
        config = read_settings()
        config.pop('rules')
        invalid.append(config)
        config = read_settings()
        config['rules'].append(dict(id='bad-regex',action='text',selector='p',pattern='[',replacement=''))
        invalid.append(config)
        config = read_settings()
        config['rules'].append(dict(id='bad-replacement',action='text',selector='p',pattern='x',replacement=r'\9'))
        invalid.append(config)
        config = read_settings()
        config['rules'].append(deepcopy(config['rules'][0]))
        invalid.append(config)
        for index, config in enumerate(invalid):
            with self.subTest(index=index):
                with self.assertRaises(MODULE.ConfigurationError):
                    MODULE.clean_html(original, 'normal', config)
                command = MODULE.CleanHtml()
                command.view = View(original)
                with patch.object(MODULE, 'get_cleanhtml_config', return_value=config):
                    command.run(None)
                self.assertEqual(command.view.value, original)
                self.assertEqual(command.view.replacements, 0)
                self.assertEqual(command.view.commands, [])

    def test_runtime_settings_are_loaded_without_python_defaults(self):
        config = MODULE.get_cleanhtml_config()
        self.assertEqual(config, read_settings())
        self.assertFalse(hasattr(MODULE, 'DEFAULT_CLEANHTML_CONFIG'))
        disabled = deepcopy(config)
        disabled['rules'] = []
        output, _ = MODULE.clean_html('<p data-mce-style="x">Text</p>', 'normal', disabled)
        self.assertIn('data-mce-style', output)

    def test_configuration_is_not_mutated(self):
        config = read_settings()
        before = deepcopy(config)
        MODULE.clean_html('<p>Text</p>', 'normal', config)
        self.assertEqual(config, before)

    def test_one_document_parse(self):
        with patch.object(MODULE, 'BeautifulSoup', wraps=MODULE.BeautifulSoup) as parse:
            MODULE.clean_html('<p><p>Text</p></p><a href="https://example.com">Link</a>', 'normal', read_settings())
            self.assertEqual(parse.call_count, 1)

    def test_empty_policy_is_configurable(self):
        config = read_settings()
        config['empty_elements']['protect_selectors'] = []
        config['empty_elements']['preserve_nbsp_in_attributed_tags'] = False
        output, _ = MODULE.clean_html('<strong class="x">&nbsp;</strong><span></span>', 'normal', config)
        self.assertEqual(canonical_html(output), '<span></span>')

    def test_nested_tables_preserve_cell_html(self):
        source = '<table><tr><td>Outer<table><tr><th>Inner</th><td><em>Value</em></td></tr></table></td><td>End</td></tr></table>'
        output, _ = MODULE.clean_html(source, 'table', read_settings())
        soup = BeautifulSoup(output, 'html.parser')
        self.assertFalse(soup.find(['table','tr','td','th']))
        self.assertEqual(soup.h3.get_text(), 'Inner')
        self.assertEqual(soup.em.get_text(), 'Value')
        self.assertIn('Outer', soup.get_text())
        self.assertIn('End', soup.get_text())

    def test_prose_regex_excludes_configurable_ancestors(self):
        config = read_settings()
        config['text_exclude_selectors'].append('.literal')
        config['rules'].append(dict(id='replace-test',action='text',selector='*',pattern='Old',replacement='New'))
        output, _ = MODULE.clean_html('<p>Old</p><div class="literal"><p>Old</p></div>', 'normal', config)
        self.assertEqual(canonical_html(output), '<p>New</p><div class="literal"><p>Old</p></div>')

    def test_working_testbed_repeat_run_all_modes(self):
        source = (PROJECT_ROOT / 'testbed.html').read_text()
        for mode in read_settings()['modes']:
            with self.subTest(mode=mode):
                first, _ = MODULE.clean_html(source, mode, read_settings())
                second, _ = MODULE.clean_html(first, mode, read_settings())
                self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main(verbosity=2)
