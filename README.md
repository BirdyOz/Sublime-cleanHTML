# CleanHTML for Sublime Text

`CleanHTML` is a Sublime Text command for tidying strict HTML files, especially HTML produced by Moodle ATTO and similar editor-driven workflows.

Unlike `CleanMD`, this package assumes the document is HTML rather than mixed Markdown.

Use `CleanHTML` for full HTML documents. For mixed Markdown files with embedded HTML blocks, use `CleanMD`.

## Settings

`CleanHTML` includes a package settings file:

- [`CleanHTML.sublime-settings`](/Users/gbird/Library/Application%20Support/Sublime%20Text/Packages/CleanHTML/CleanHTML.sublime-settings)

The current settings control:

- whether external links are normalised with safe `target` / `rel` attributes
- whether invalid nested paragraph wrappers are repaired
- whether embedded audio is hoisted to the top of the document for legacy workflows
- whether `htmlprettify` runs after cleanup
- which matched elements are unwrapped with BeautifulSoup CSS selectors
- which matched elements are removed entirely with BeautifulSoup CSS selectors
- which attributes are removed by exact name or `*` wildcard
- which empty elements receive a non-breaking space for TinyMCE preservation

TinyMCE defaults in `CleanHTML.sublime-settings`:

```json
"remove_attributes": ["data-mce-*"],
"preserve_nbsp_placeholders": true,
"protect_empty_selectors": ["div", "span", "i"]
```

Add exact attribute names or wildcard patterns to `remove_attributes`, for
example `["data-mce-*", "data-editor-*", "contenteditable"]`. Matching uses
the complete attribute name, is case-insensitive, and treats only `*` as a
wildcard. Values, real `src`/`style` attributes, and unrelated `data-*`
attributes are preserved unless explicitly listed. Set the list to `[]` to
disable this removal in every mode. Selector cleanup runs before attribute
removal, so selectors can still match the original attributes.

Empty `div`, `span`, and `i` elements gain a non-breaking space and survive
structural unwrapping, including MP mode's span cleanup. Extend or narrow
`protect_empty_selectors` with CSS selectors such as `span.component__icon`.
Only whitespace-only elements with no child elements are padded; void tags
such as `img` are never padded. Existing NBSP placeholders in otherwise-empty
attributed elements are also retained when `preserve_nbsp_placeholders` is
true. Ordinary NBSP text becomes regular spaces, and blank paragraphs still
clean up. BeautifulSoup may emit the actual Unicode NBSP character rather
than the spelling `&nbsp;`; these are equivalent HTML content.

Explicit removal selectors and table-mode table unwrapping still take
precedence. To restore the previous placeholder cleanup, use
`"protect_empty_selectors": []` and `"preserve_nbsp_placeholders": false`.
Confirm preservation after saving through your Moodle TinyMCE editor as well
as in Sublime; editor configuration can affect the roundtrip.

Selector examples you can add over time include:

- `div.delete-me`
- `a[name]`
- `li > p`
- `div.legacy-wrapper > span`

## What CleanHTML does

`CleanHTML` runs across the whole file and applies a sequence of substitutions, tag removals, and final HTML prettification.

Core cleanup includes:

- normalising ordinary `&nbsp;` text and removing common editor artefacts such as `data-mce-*`, YUI ids, redundant `dir="ltr"`, and some default inline styles
- removing or simplifying unnecessary wrapper tags such as `span`, `section`, `article`, empty `div`, and several empty inline/block tags
- stripping bullet-like prefixes from `<li>` content
- removing Moodle image timestamp suffixes
- cleaning up specific attribution helper markup
- normalising external links so `http` and `https` links get `target="_blank"` and `rel="noopener noreferrer"`
- repairing invalid nested paragraph wrappers such as `<p><p>...</p></p>`
- applying a first-pass BeautifulSoup structural cleanup for selected wrapper and malformed tags
- unwrapping or removing extra elements via settings-driven CSS selectors
- moving embedded `<audio>` blocks to the top of the document when required by the existing workflow

After substitutions, the package performs structural tag cleanup and then runs HTML prettification.

Each run also reports a short summary in the status bar and Sublime console, including the cleaning mode, number of substitutions, and number of tags removed.

## Cleaning Modes

The package provides multiple cleaning modes:

- `normal`
  Standard HTML cleanup for editor-generated markup.

- `deep`
  Normal cleanup plus additional deep substitutions.

- `canvas`
  Canvas-specific cleanup rules, including comment and editor-attribute removal.

- `table`
  Deep cleanup plus aggressive table-tag removal.

- `mp`
  Melbourne Polytechnic-specific cleanup, including conversion of some paragraph-based bullets into list markup and a number of content transformations.

- `mpextended`
  Extension point for additional Melbourne Polytechnic-specific substitutions.

## Commands

Command palette entries currently provided:

- `BirdyOz - Clean HTML (normal)`
- `BirdyOz - Clean HTML (normal, no prettify)`
- `BirdyOz - Clean HTML (Deep)`
- `BirdyOz - Clean HTML (Canvas)`
- `BirdyOz - Clean HTML (Table plus Deep)`
- `BirdyOz - Clean HTML (Melb Poly)`
- `BirdyOz - Clean HTML (Melb Poly - Extended)`

## Dependencies

This package relies on other Sublime Text packages for parts of the workflow:

- [HTML-CSS-JS Prettify](https://packagecontrol.io/packages/HTML-CSS-JS%20Prettify) for final HTML prettification

It also uses BeautifulSoup internally for targeted HTML repairs, safer link handling, and structural cleanup.

## Usage

1. Open a strict HTML file.
2. Run the appropriate `Clean HTML` command from the Command Palette.
3. Choose the cleaning mode that matches the content source.

Because the command runs across the full document, it is best used on working copies or source files that are intended to be rewritten in-place.

If you want to inspect the structural cleanup before final formatting, use:

- `BirdyOz - Clean HTML (normal, no prettify)`

## Test Assets

The package includes:

- [`testbed.html`](/Users/gbird/Library/Application%20Support/Sublime%20Text/Packages/CleanHTML/testbed.html)
- [`testplan.md`](/Users/gbird/Library/Application%20Support/Sublime%20Text/Packages/CleanHTML/testplan.md)

These remain the manual, in-Sublime regression aids for full command modes and
HTMLPrettify integration.

The project-owned headless-safe suite is visible under `tests/`:

- `tests/clean_html_cases.py` contains the executable link and structural cases.
- `tests/test_clean_html.py` supplies narrow Sublime API stubs and runs 24
  regressions, including the TinyMCE command pipeline in all six modes.

Run it from the project root with:

```zsh
/Users/gbird/.venvs/workbench/bin/python -m unittest -v tests/test_clean_html.py
```

Or open `tests/test_clean_html.py` in Sublime and choose **Build With →
PyBuild**. Run the complete project gate, including syntax compilation, with:

```zsh
/Users/gbird/.venvs/workbench/bin/python \
  /Users/gbird/Dropbox/github/pybuild/scripts/run_plugin_smokes.py \
  --project CleanHTML
```

As of 2026-09-24, that gate passes all 15 headless regressions and the
declared syntax checks. It does not replace the required in-Sublime check for
package loading, command/menu/keybinding behaviour, HTMLPrettify integration,
or complete mode coverage; use a working copy of `testbed.html` and
`testplan.md` for those checks.

## Keyboard Shortcuts

Default macOS shortcuts:

- <kbd>CMD</kbd> + <kbd>Shift</kbd> + <kbd>\\</kbd> for normal mode
- <kbd>CMD</kbd> + <kbd>Opt</kbd> + <kbd>\\</kbd> for deep mode
- <kbd>CMD</kbd> + <kbd>Shift</kbd> + <kbd>Opt</kbd> + <kbd>\\</kbd> for table mode
