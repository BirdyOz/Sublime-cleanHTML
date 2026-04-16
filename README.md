# CleanHTML for Sublime Text

`CleanHTML` is a Sublime Text command for tidying strict HTML files, especially HTML produced by Moodle ATTO and similar editor-driven workflows.

Unlike `CleanMD`, this package assumes the document is HTML rather than mixed Markdown.

## Settings

`CleanHTML` includes a package settings file:

- [`CleanHTML.sublime-settings`](/Users/gbird/Library/Application%20Support/Sublime%20Text/Packages/CleanHTML/CleanHTML.sublime-settings)

The current settings control:

- whether external links are normalised with safe `target` / `rel` attributes
- whether invalid nested paragraph wrappers are repaired
- whether embedded audio is hoisted to the top of the document
- whether `htmlprettify` runs after cleanup
- which matched elements are unwrapped with BeautifulSoup CSS selectors
- which matched elements are removed entirely with BeautifulSoup CSS selectors

Selector examples you can add over time include:

- `div.delete-me`
- `a[name]`
- `li > p`
- `div.legacy-wrapper > span`

## What CleanHTML does

`CleanHTML` runs across the whole file and applies a sequence of substitutions, tag removals, and final HTML prettification.

Core cleanup includes:

- removing common editor artefacts such as `&nbsp;`, YUI ids, redundant `dir="ltr"`, and some default inline styles
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

These are intended as manual regression aids rather than an automated test harness.

## Keyboard Shortcuts

Default macOS shortcuts:

- <kbd>CMD</kbd> + <kbd>Shift</kbd> + <kbd>\\</kbd> for normal mode
- <kbd>CMD</kbd> + <kbd>Opt</kbd> + <kbd>\\</kbd> for deep mode
- <kbd>CMD</kbd> + <kbd>Shift</kbd> + <kbd>Opt</kbd> + <kbd>\\</kbd> for table mode
