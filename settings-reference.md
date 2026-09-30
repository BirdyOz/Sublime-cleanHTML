# CleanHTML settings reference

Edit `CleanHTML.sublime-settings` directly. It owns all active cleanup policy;
the plugin has no parallel dictionary of default transformations. Sublime-style
`//` and `/* ... */` comments are supported; keep commas and quoted strings
valid JSON and avoid trailing commas for the headless loader. Rules reload for
each command; no restart is needed for a settings edit.

## Quick edits: grouped settings

The saved `rules` object contains `order` (group names in execution order) and
`groups` (definitions). Each group supplies an `action`, optional `defaults`,
and an ordered `entries` list. Each entry is a single-key object: its key is
its unique rule ID, and its value describes the operation. IDs are unique
across all groups, not just within one group.

**Keep entries as a list.** Sublime alphabetizes object keys; a mapping of all
entries would silently change their execution order. The single-key objects
inside the list retain readable names without relying on object key order.

A simple remove or unwrap entry can be a CSS selector:

```json
{"my-wrapper": "aside.wrapper"}
```

Add that line to `unwrap.entries` to keep its contents, or `remove.entries`
to delete it and its contents. Use an object to supply guards/options:

```json
{"bare-wrapper": {"selector": "aside", "bare": true}}
```

Attributes and classes share selector `*` in their saved group defaults. An
entry can override it, and defaults are replaced per field (not deep-merged):

```json
{"other-editor-attributes": {"remove": ["data-editor-*", "contenteditable"]}}
{"image-class": {"selector": "img", "replace": {"old-class": "new-class"}}}
{"default-margin": {"selector": "[style]", "remove": {"margin": ["0px"]}}}
```

These are separate entry examples for attributes, classes and styles,
respectively. Add commas when inserting them into their lists. Attribute
names support `*` wildcards; class names are exact tokens, and styles match
property/value pairs. Unrelated values survive.

Text entries support compact pairs:

```json
{"my-label": ["Old label", "New label"]}
{"paragraph-label": ["Old", "New", {"selector": "p", "modes": ["deep"]}]}
```

The optional third object overrides shared defaults and supplies options such
as `enabled`, `modes`, `scope` or `skip_placeholders`. It cannot redefine the
find/pattern or replacement. In a group with `match: "regex"`, pairs are
`[pattern, replacement]`; otherwise they are literal `[find, replacement]`.
For a regex inside the saved mixed substitutions group, use an explicit object:

```json
{"my-regex": {"pattern": "\\bOld term\\b", "replacement": "New term"}}
```

To disable an object entry, add `"enabled": false`. A selector string becomes
`{"selector": "aside", "enabled": false}` when you need options. A pair can
use a third object containing `"enabled": false`. Disabled rules are validated
before execution too. Unknown keys/actions, malformed pairs, invalid selectors,
regexes and replacement backreferences fail before buffer editing.

To add a group, give it an action and entries, optional shared defaults, and
add its name to `rules.order` exactly once. Ordinarily add rules to an existing
group instead. Later attribute/class/text groups intentionally preserve
execution dependencies: do not merge them into earlier passes merely because
their actions match. All remove actions execute first regardless of position.

Python expands the saved groups into the same validated action handlers used
previously. Flat lists remain accepted for programmatic overrides and existing
verification fixtures; the saved policy lives only in the grouped settings.

## Top-level settings

All seven fields are required; missing configuration does not activate fallback
cleanup rules.

| Key | Purpose |
|---|---|
| `schema_version` | Current schema is `1` |
| `modes` | Unique nonempty mode names; the first is the command's default |
| `run_htmlprettify_after_clean` | Request final `htmlprettify`; the no-prettify palette entry overrides this for its invocation |
| `output_formatter` | BeautifulSoup `html` or `minimal`; `html` spells NBSP as `&nbsp;` |
| `text_exclude_selectors` | Exclude matching elements and descendants from text rules, wrapper simplification, and empty cleanup |
| `empty_elements` | Final empty-tag preservation, removal selectors and padding |
| `rules` | Group definitions and their explicit execution order |

The mode names in palette/keymap files must agree with `modes`. Retired `mp`
and `mpextended` names are rejected by the saved configuration. Adding a mode
in settings makes it callable through the command API; a palette entry is a
separate UI edit.

## Execution order and boundaries

All enabled `remove` actions run first, in their own listed order, so deletion
wins over unwrapping. All other enabled rules run in `rules.order` group order and then entry-list order. Each
selector sees the tree as it exists at that stage. Keep selectors depending on
editor attributes before those attributes are deleted.

Empty-element cleanup runs bottom-up before the first structural unwrap/table
rule and once more at the end. This protects elements made empty by deleting
children and removes newly empty ancestors without requiring another command
run. Protection is evaluated against the final meaningful attributes/policy,
not a cached set of editor-only attributes. Explicit removals can delete a
protected element.

Text-node smoothing joins adjacent strings created by tree edits before a
text rule. Configured whitespace rules stabilize whitespace-only nodes after
unwrapping without changing preformatted content. Full-document line joining
and raw-document regex are not used.

Regex flags are `IGNORECASE`, `MULTILINE`, and `DOTALL`, supplied as a `flags`
list. Patterns/replacements use Python regex syntax, with JSON backslash
escaping: `"\\d+"` is a digit pattern and `"\\1"` is a replacement group.
All remaining cleanup regex patterns, including formatting patterns, live in
settings. The tiny regex used internally for `*` attribute-name matching is
matcher plumbing, not a hidden replacement rule.

## Action reference

The following describes expanded engine rules. In grouped settings, the entry
key supplies `id`, the group supplies `action`, and entry fields override its
defaults. Do not add id/action fields inside entry values. The examples below
use the saved grouped-entry format and can be added to the indicated entries list.
Except `comments` and `comment_lines`, actions require a CSS `selector`.

| Action | Fields and behavior |
|---|---|
| `remove` | Delete selected tags and contents; optional `text_equals` requires exact combined text; `children_selector` requires matching child elements with no other meaningful text |
| `unwrap` | Remove selected wrapper only; optional `bare` requires no attributes, `only_child` requires the sole element with no meaningful sibling text, `children_selector` requires all element children to match with no meaningful direct text |
| `unwrap_nested` | `children_selector`; unwrap a wrapper containing only matching child elements and whitespace/comments |
| `remove_trailing` | `children_selector`; remove matching trailing children, stopping at other content; never consumes following text |
| `attributes` | `remove` name patterns, `remove_empty` exact names, `remove_matching` mapping names to whole-value regexes, `set` mapping names to text values; optional regex flags |
| `classes` | `remove` exact tokens, `replace` token mapping, `add` tokens; preserves unrelated tokens and avoids duplicates |
| `styles` | `remove` maps CSS properties to exact value lists; removes declarations, retaining unknown declarations/quoted delimiters/comments |
| `query` | `attribute`, `remove_patterns`; remove only whole matching URL query terms, preserving other terms, fragments and original escaping; optional flags |
| `regex_attribute` | `attribute`, `pattern`, `replacement`, optional flags; runs on that attribute value only |
| `text` | `replacement`, exactly one of literal `find` or regex `pattern`; optional flags, `scope` (`all` or `leading`), `skip_placeholders` |
| `comments` | Remove comments; optional `pattern`/flags restrict content; respects excluded ancestors |
| `comment_lines` | Put matching comments on separate lines; optional `pattern`/flags restrict content; respects excluded ancestors |
| `links` | `schemes`, `target`, `rel`, `internal_remove`; merge required external rel tokens and apply the configured internal removal policy |
| `move_to_start` | `destination` selector and `separator` object with `tag`/`attributes`; move selected nodes in order to destination or fragment root; saved audio rule is disabled |
| `flatten_table` | See the table fields below; removes configured wrappers while retaining their contents |

Selectors are CSS, not regex. E.g. `[dir="ltr"]` scopes attribute removal by
value; `img` scopes a class mapping to images. Glob attribute-name patterns
and regex value patterns are deliberately separate.

CSS removal compares property names/value text case-insensitively after outer
whitespace trimming. It does not normalize every equivalent CSS value or strip
`!important` implicitly. Add a separate value such as `1rem !important` if
needed. The scanner respects quotes, escapes, comments and brackets; it is a
conservative declaration editor, not a CSS validator. Unrecognized syntax is
retained.

Text rules visit each selected descendant text node once, even if selectors
match both a parent and child. `leading` chooses the first non-whitespace text
node, including inside an inline wrapper. A match cannot span separate text
nodes: this protects markup and lets you target what is actually present.
Explicit removal/attribute actions still operate on real selected elements;
text exclusions do not act as a blanket exemption from all configured actions.

### Scoped style edits

```json
{"default-styles": {"selector": "[style]", "remove": {"font-size": ["1rem", "16px"], "text-align": ["left", "start"]}}}
```

Use this entry in `styles.entries`. The brackets around `["1rem", "16px"]`
are an array you can extend. The brackets in `"[style]"` are part of a quoted
CSS selector meaning elements with a style attribute; they are not an array.
Add another property to the remove map to cover it, e.g. `"margin": ["0", "0px"]`.
This preserves `color: red` when it shares an attribute with `font-size: 1rem`.

### Literal and regex substitutions

The settings file presents each substitution as one compact named entry, preceded
by a plain-language comment. Their groups share `rules.order` with structural
operations: URL substitutions precede link handling, and final whitespace
substitutions follow table conversion. Keep that order when editing.
`find` matches literal text; `pattern` matches a Python regex. `replacement`
is the new text (an empty string deletes the match). `scope: "leading"`
limits a rule to the start of the selected element's text. Optional `modes`
limits which commands run a substitution.


Add these named entries to `substitutions.entries`:

```json
{"rename-label": ["Old label", "New label", {"selector": "p.notice"}]}
```

```json
{"rename-code": {"selector": "p.notice", "pattern": "Code (\\d+)", "replacement": "Reference \\1", "flags": ["IGNORECASE"]}}
```

Place new text rules before the final whitespace-normalization rules. Avoid
patterns that discard numeric signs or assume HTML attribute order. No eval,
Python callbacks, or arbitrary executable code is accepted in settings.

## Empty elements and TinyMCE

`empty_elements` requires:

- `protect_selectors`: initially `div`, `span`, and `i`.
- `remove_selectors`: known empty paragraphs/list/emphasis/headings to remove.
- `preserve_nbsp_in_attributed_tags`: keep existing padding in otherwise-empty
  attributed tags after editor attributes have been removed.
- `preserve_attributes`: attribute-name patterns whose empty destinations/ARIA
  semantics must remain; saved policy includes IDs/names/ARIA/roles.
- `padding`: nonempty text; saved value is NBSP (`\u00a0`).

Protected empty non-void elements receive padding. Images and other void tags
are never padded. Real child elements prevent an element from being treated as
empty. Protected text/structural contexts are left untouched. A tag containing
only removed `data-mce-*` attributes does not become a permanent placeholder
unless it matches another protection policy.

To protect only icon classes, change `protect_selectors` to e.g.
`["span.component__icon", "i.fa", "div.clearfix"]`. To stop preserving empty
fragment/ARIA targets as well, change `preserve_attributes` deliberately.
Finally verify saved content through Moodle TinyMCE: CleanHTML's preservation
is not proof of every editor configuration's behavior.

## Table fields

The saved `table-flattening` rule is scoped to mode `table`:

- `row_selector`: identifies rows.
- `cell_selector`: identifies header/data cells.
- `caption_selector`: identifies captions to retain.
- `plain_header_selector`: identifies header cells eligible for heading conversion.
- `plain_header_tag`: saved as `h3`; used only if the header has nonempty text
  and no child HTML elements. Headers containing HTML retain their inner HTML.
- `cell_separator`: saved as a space between neighboring cells.
- `row_separator`: saved as a newline between rows/captions.
- `unwrap_selectors`: table, tbody, thead, tfoot, tr, td, th and caption.
- `remove_selectors`: column/column-group tags; they have no cell content.

Cell contents are moved as nodes, not flattened through `get_text()`. The new
header retains its text but discards the original table-cell attributes along
with the table markup. Nested tables are processed from the inside out.
Table mode still runs common/deep cleanup first; disable particular rules if
that policy should differ. The rule is a table-markup removal workflow, not a
conversion to lists, CSV or a replacement table design.

## Intentional changes from the historical cleaner

- Meaningful BRs survive; paragraphs containing only BRs are deleted, and trailing
  paragraph BRs are removed without deleting an adjacent character.
- Named anchors, meaningful attributed heading wrappers, and multiple list
  paragraphs survive. A sole bare LI paragraph can still be unwrapped.
- Timestamp rules are image-query rules; they no longer alter prose/other URLs.
- CSS/class cleanup is scoped, preserving unrelated declarations/tokens.
- Empty structural cleanup is stable across repeated runs with saved settings.
- MP/MP Extended and global Canvas numeric migration are archived in
  `legacy-mp-transformations.md` and are not active.
- Source-formatting regexes that inserted blank lines around tags were retired;
  final layout belongs to HTMLPrettify. Remaining whitespace-node rules are in
  settings and can be disabled.

Image-only paragraphs are unwrapped by `paragraph-only-image`; paragraphs
containing images alongside meaningful text keep their wrapper.

### Structural comment line breaks

`comment_lines` inserts line boundaries around matching HTML comments. Its
optional `pattern` and `flags` filter comment text; omitting the pattern selects
all comments outside excluded elements. The saved rule selects Start/End of
comments and runs after whitespace normalization. HTMLPrettify preserves the
inserted breaks. Disable `structural-comment-lines` to retain inline placement.

## Indentation and editor settings

CleanHTML performs structural cleanup; HTML-CSS-JS Prettify handles final
indentation. To use two spaces for formatted HTML, set `indent_size: 2`,
`indent_char: " "` and `indent_with_tabs: false` in the HTML section of
`Packages/User/.jsbeautifyrc`. Preserve other formatter options.

Sublime application preferences `tab_size: 2` and
`translate_tabs_to_spaces: true` set editing defaults for all syntaxes.
Syntax/project/view settings and indentation detection can override them.
Repeat them in HTML or Markdown syntax settings only if that syntax needs an
explicit override. Existing text is not automatically reindented by changing
the preferences.

With HTMLPrettify's `use_editor_indentation: false`, formatter indentation
comes from its own configuration (and applicable EditorConfig), not the editor
preferences. Keep both in agreement. No CleanHTML Python change is needed.
These are configuration instructions, not a claim that User settings were edited.

To inspect bundled HTML defaults, run in Sublime's console:

```python
window.run_command("edit_settings", {"base_file": "${packages}/HTML/HTML.sublime-settings"})
```

The bundled HTML file mainly describes completions. Preferences → Settings
shows the broader editor options with comments; applicable values can also be
set in a syntax-specific file. HTMLPrettify's layout options remain separate.
