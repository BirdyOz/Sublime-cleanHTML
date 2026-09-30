# CleanHTML manual regression plan

Use scratch copies of `testbed.html` and pristine inputs from
`tests/clean_html_cases.py`. Never overwrite the working fixture merely to test.
Run **BirdyOz - Clean HTML (normal, no prettify)** first to isolate structural
cleanup; then check the final formatting path. Settings policy and rule fields
are documented in `settings-reference.md`.

## Content preservation

1. Run normal on `<div></div><span></span><i class="icon"></i>`.
   All three survive with `&nbsp;`. Repeat cleanup: no additional padding.
   Existing attributed NBSP placeholders and named anchors also survive.
2. Remove `data-mce-style`, `data-mce-src` and other `data-mce-*` attributes;
   retain ordinary `style`, `src`, `alt`, other data attributes and inner HTML.
   Add an attribute wildcard to the settings rule and confirm its exact scope.
3. Keep unrelated CSS declarations, class tokens and URL query terms. Remove
   configured declarations/tokens only. Image timestamp cleanup must retain
   other query parameters and fragments; timestamps in prose remain unchanged.
4. Preserve PRE indentation, code, scripts, styles and textarea text, including
   optional markers and NBSP. Confirm normal cleanup does not join document lines.
5. Preserve multiple paragraphs inside list items, styled paragraph wrappers,
   negative numbers and ordinary zeros. Remove configured leading list markers.
6. Preserve meaningful BRs and text immediately after a BR. Remove only the
   configured bogus/trailing BRs and whole paragraphs containing only BRs.
   Unwrap image-only paragraphs, retaining image attributes; keep paragraphs
   that mix images with text. Explicit removal selectors win over unwrap.
7. Preserve existing external rel tokens while adding configured link protection.
   Internal target/rel removal follows its settings rule. Named anchors survive.

## Table mode

Run table mode on:

```html
<table>
  <caption><em>Caption</em></caption>
  <thead><tr><th>Plain heading</th><th><strong>Formatted heading</strong></th></tr></thead>
  <tbody><tr><td><p>First</p></td><td><em>Second</em></td></tr></tbody>
  <tfoot><tr><td>Footer</td></tr></tfoot>
</table>
```

There must be no table, caption, table-section, row or cell wrappers remaining.
Plain heading becomes `<h3>Plain heading</h3>`. The formatted header retains
`<strong>Formatted heading</strong>`; paragraph/emphasis/caption content survives.
Column markup is removed. Cell and row boundaries use the configured separators.
Nested tables preserve their inner HTML too. Normal mode preserves table markup.
Repeat both structural cleanup and the HTMLPrettify path to check stability.

## Modes and optional rules

- Normal is the first configured/default mode; deep also replaces `[OPTIONAL]`
  in prose. Excluded code retains it.
- Canvas removes configured comments/targets; ordinary numbers and URLs remain.
- MP and MP Extended are absent from the palette. Their substitutions are
  archived in `legacy-mp-transformations.md` and are not active rules.
- For audio testing, temporarily enable the rule with id `audio-hoisting`.
  Audio elements retain their order and move to the start of body/fragment
  content, followed by the configured separator. Doctype stays before HTML.
  Restore the rule's saved `enabled: false` afterward.

## Settings and editor integration

- Disable a rule, run cleanup, restore it, then confirm the next command loads
  the change without restarting Sublime.
- Introduce an invalid selector, regex, replacement backreference or setting
  type in a temporary override: cleanup reports the rule/key and leaves the
  buffer unchanged. Restore valid settings.
- Check all retained palette entries, shared BirdyOz menu entries and existing
  key bindings. Check both no-prettify and configured HTMLPrettify output.
- Confirm caret and multiple/reversed selections remain usable after cleanup;
  one Undo restores the structural edit. A second unchanged cleanup should
  create no additional structural edit. HTMLPrettify may have its own edit.
- Paste cleaned HTML into Moodle TinyMCE, save and reopen. Confirm empty
  div/span/i placeholders, headings, images, links and formatted cell content
  survive, then clean the returned HTML to remove regenerated editor attributes.

## Verification record — 2026-09-30

The shared PyBuild gate passes 15 test methods, including 69 shared fixtures,
all four working-testbed repeated-run checks, adapter/configuration checks and
all four declared syntax targets. Two suites pass with no skips or informational
suites.

Before the later paragraph/comment and grouping updates, native Sublime execution passed 66 checks: 60 shared fixtures using the actual
command and repeated execution, invalid-settings buffer preservation, all four
testbed modes, and table cleanup followed by HTMLPrettify. The formatting check
confirms plain header H3, formatted header/cell HTML, NBSP and PRE indentation.

Keyboard/menu entry points, undo behavior and a Moodle TinyMCE save/reopen
roundtrip remain manual checks. No saved audio-setting change was made.

Grouped settings verification confirms expansion matches the previous effective
rule order and values. Tests cover shared defaults, selector/object/pair entries,
optional pair options, invalid groups and duplicate IDs. Native inspection
confirmed Sublime alphabetizes object keys, so group and entry order are explicit
arrays. A native rerun of the latest grouping remains pending after active
editor interaction interrupted the automation.
