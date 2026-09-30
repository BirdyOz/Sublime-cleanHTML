# CleanHTML for Sublime Text

CleanHTML rewrites a whole strict-HTML document, especially Moodle TinyMCE/ATTO
content. For mixed Markdown with embedded HTML, use CleanMD.

## Settings are the cleanup policy

[`CleanHTML.sublime-settings`](CleanHTML.sublime-settings) is the single source
of truth for active rules, selectors, class/style/attribute edits, text and URL
regex patterns, replacements, modes, and empty-element preservation. Python
contains validation and generic transformation handlers, not a duplicate
`DEFAULT_CLEANHTML_CONFIG` or hardcoded substitution lists.

Rules are grouped by operation, with shared defaults and compact named entries.
Text substitutions accept find/replace pairs. Edit/add an entry or set
`"enabled": false` in its options to disable it. Changes are
loaded on the next command. `rules.order` and entry lists preserve execution
order even though Sublime alphabetizes object keys. No separate User settings
file is needed. See
[settings-reference.md](settings-reference.md) for action fields and examples.
The file uses Sublime’s JSON-with-comments format. Inline comments explain
every saved rule, and substitutions use one compact object per line. The
headless loader ignores comments while preserving URL and regex strings.
Invalid settings leave the document unchanged and identify the
failing key/rule in the Sublime console/status message.

The saved rules:

- Remove `data-mce-*`, YUI IDs, known overlays and ReadSpeaker artifacts.
- Remove exact redundant class tokens, attributes and style declarations,
  preserving unrelated styles/classes and meaningful empty image `alt`.
- Normalize absolute HTTP(S) links with target/rel while preserving existing
  external rel tokens. Internal target/rel removal is explicitly configurable.
- Repair nested paragraph wrappers and simplify selected structural wrappers.
- Preserve meaningful BRs, named anchors, multiple paragraphs in list items,
  and whitespace-sensitive content. Known bogus/trailing editor BRs are
  removed without consuming adjacent text. BR-only paragraphs are deleted;
  image-only paragraphs are unwrapped, retaining the images.
- Add NBSP to empty `div`, `span`, and `i`, including elements emptied by
  cleanup. Preserve meaningful empty targets/ARIA attributes and existing
  attributed NBSP placeholders after editor attributes are removed.
- Put structural `Start of…` / `End of…` comments on separate lines.
- Apply remaining text regexes to scoped text nodes and timestamp regexes to
  image URL query terms; no cleanup regex scans the whole HTML document.

`pre`, `code`, `script`, `style`, and `textarea` are excluded from text cleanup,
structural simplification and empty cleanup through configured selectors.
Explicit removal rules still take precedence. HTML serialization can change
quotes, entity spelling and attribute order; NBSP is emitted as `&nbsp;` with
the saved HTML formatter.

The cleaner validates first, parses once, runs explicit removals before
other rules, applies remaining rules in order, finalizes empty elements,
serializes once, and replaces the buffer once if it changed. It preserves an
appropriate clamped caret/selection instead of selecting/joining the document.
The console reports per-rule counts. HTMLPrettify is an optional separate final
formatting step; the status says when it was requested.

## Modes and commands

| Mode | Saved behavior |
|---|---|
| `normal` | Common structural, attribute, style, link and text cleanup |
| `deep` | Normal plus the configured `[OPTIONAL]` text replacement |
| `canvas` | Common cleanup plus comment removal and external target removal |
| `table` | Deep plus table unwrapping; plain-text `th` becomes `h3` |

Table mode removes the table/section/row/cell/caption wrappers and column tags,
retaining the HTML inside cells. A plain-text header becomes an `h3`; a header
containing HTML retains that HTML. A space separates neighboring cells and a
newline separates rows. The header tag and separators are settings fields.

Palette entries retain the `BirdyOz - Clean HTML` names, including **normal,
no prettify** for inspecting structural cleanup. The shared BirdyOz menu reads
these same command entries. Existing macOS shortcuts remain:

- Cmd+Shift+Backslash: normal.
- Cmd+Option+Backslash: deep.
- Ctrl+Option+Backslash: Canvas.
- Cmd+Shift+Option+Backslash: table.

MP and MP Extended have been retired. Their exact historical substitutions
and reuse cautions are in [legacy-mp-transformations.md](legacy-mp-transformations.md).
The historic global Canvas number migration is also archived there; it is no
longer active. Audio hoisting remains as a disabled settings rule.

## Indentation

Set HTMLPrettify’s HTML `indent_size` to `2` for two-space formatted output.
Sublime’s application `tab_size` and `translate_tabs_to_spaces` control editing
defaults across syntaxes; they do not override the formatter while
`use_editor_indentation` is false. See the indentation section in
[settings-reference.md](settings-reference.md). CleanHTML has no indentation
width setting.

## Dependencies and verification

BeautifulSoup and SoupSieve must be available in Sublime's embedded runtime.
[HTML-CSS-JS Prettify](https://packagecontrol.io/packages/HTML-CSS-JS%20Prettify)
is needed when final formatting is enabled. Keep the `.python-version` selector
at `3.8`; shell Python is not evidence of Sublime runtime compatibility.

Executable fixtures are under `tests/`; they load the repository settings,
cover cleanup and preservation, and check repeated-run stability. The adapter
tests also check one parse, at most one buffer replacement, selections, invalid
settings, retired modes, and prettify dispatch. The headless stub loader
restores global modules and must not be used as a live Sublime test runner.

```zsh
/Users/gbird/.venvs/workbench/bin/python -m unittest -v tests/test_clean_html.py

/Users/gbird/.venvs/workbench/bin/python \
  /Users/gbird/Dropbox/github/pybuild/scripts/run_plugin_smokes.py \
  --project CleanHTML
```

[pybuild-smokes.toml](pybuild-smokes.toml) owns the shared gate.
[testplan.md](testplan.md) covers native commands, formatting and Moodle
roundtrip checks. [testbed.html](testbed.html) is a mutable working fixture:
use a scratch copy, and use the executable cases for pristine inputs.
