# CleanHTML Test Plan

This file records representative manual regression cases for `GB-clean-HTML.py`.

Each case includes:

- `MODE`: the command mode to run (`normal`, `deep`, `table`, `canvas`, `mp`, or `mpextended`)
- `INPUT`: sample source HTML
- `EXPECTED`: the intended result after running `CleanHTML`

These examples remain the manual review checklist for complete command modes
and HTMLPrettify integration. The headless-safe subset is executable from the
project-owned `tests/clean_html_cases.py` and `tests/test_clean_html.py` files;
do not duplicate those cases inside PyBuild or a virtual environment.

## Test 1: External links gain safe attributes

MODE: `normal`

INPUT:

```html
<p><a href="https://example.com">External</a> and <a href="/internal">Internal</a></p>
```

<!--
EXPECTED:
<p><a href="https://example.com" rel="noopener noreferrer" target="_blank">External</a> and <a href="/internal">Internal</a></p>
-->

## Test 2: Nested paragraph wrappers are repaired

MODE: `normal`

INPUT:

```html
<div class="card-body gb-bs-content">
    <p>
        <p>First paragraph.</p>
        <p>Second paragraph.</p>
    </p>
</div>
```

<!--
EXPECTED:
<div class="card-body gb-bs-content">
    <p>First paragraph.</p>
    <p>Second paragraph.</p>
</div>
-->

## Test 3: Empty and redundant editor attributes are removed

MODE: `normal`

INPUT:

```html
<p dir="ltr" style="text-align: left;" id="yui_123">Text</p>
```

<!--
EXPECTED:
<p>Text</p>
-->

## Test 4: Bullet markers are stripped from li text

MODE: `normal`

INPUT:

```html
<ul>
    <li>• One</li>
    <li># Two</li>
    <li>3. Three</li>
</ul>
```

<!--
EXPECTED:
<ul>
    <li>One</li>
    <li>Two</li>
    <li>Three</li>
</ul>
-->

## Test 5: Moodle image timestamps are removed

MODE: `normal`

INPUT:

```html
<p><img src="example.png?time1712345678" /></p>
```

<!--
EXPECTED:
<p><img src="example.png" /></p>
-->

## Test 6: Specific attribution helper cleanup still applies

MODE: `normal`

INPUT:

```html
<a class="source-btn" data-toggle="collapse" href="#show-123">▼ Show attribution</a>
```

<!--
EXPECTED:
<a class="source-btn text-muted" data-toggle="collapse" href="#show-123">▽ Show attribution</a>
-->

## Test 7: Empty paragraph wrappers around br are simplified

MODE: `normal`

INPUT:

```html
<p><br></p>
```

<!--
EXPECTED:
<br>
-->

## Test 8: Empty structural wrappers are removed by tag cleanup

MODE: `normal`

INPUT:

```html
<section><article><div><p>Content</p></div></article></section>
```

<!--
EXPECTED:
<p>Content</p>
-->

## Test 9: Deep mode applies deep substitutions in addition to normal ones

MODE: `deep`

INPUT:

```html
<p>Before [OPTIONAL] after</p>
```

<!--
EXPECTED:
<p>Before after</p>
-->

## Test 10: Canvas mode removes comments and target attributes

MODE: `canvas`

INPUT:

```html
<!-- comment -->
<p><a href="https://example.com" target="_blank">External</a><br></p>
```

<!--
EXPECTED:
<p><a href="https://example.com">External</a></p>
-->

## Test 11: MP mode converts bullet paragraphs into ul/li markup

MODE: `mp`

INPUT:

```html
<p class="bulletlist">First</p>
<p class="standardbulletpoint">Second</p>
```

<!--
EXPECTED:
<ul><li>First</li><li>Second</li></ul>
-->

## Test 12: MP mode unwraps p tags around standalone images

MODE: `mp`

INPUT:

```html
<p><img src="image.jpg" alt="Example"></p>
```

<!--
EXPECTED:
<img src="image.jpg" alt="Example">
-->

## Test 13: Table mode removes table tags after substitution and tag cleanup

MODE: `table`

INPUT:

```html
<table><tbody><tr><td>Cell</td></tr></tbody></table>
```

<!--
EXPECTED:
Cell
-->

## Test 14: Audio block is moved to the top when embedded later in the document

MODE: `normal`

INPUT:

```html
<p>Intro</p><audio controls src="audio.mp3"></audio><p>After</p>
```

<!--
EXPECTED:
<audio controls src="audio.mp3"></audio><div class="clearfix container-fluid"></div><p>Intro</p><p>After</p>
-->

## Test 15: ReadSpeaker links and icons are removed

MODE: `normal`

INPUT:

```html
<p><a href="https://app.readspeaker.com/cgi-bin/rsent?customerid=1">Listen</a></p>
```

<!--
EXPECTED:
<p></p>
-->

## Test 16: TinyMCE attributes are removed in all modes

MODE: each of `normal`, `deep`, `canvas`, `table`, `mp`, `mpextended`;
use no-prettify first, then normal with HTMLPrettify.

INPUT:

```html
<p data-mce-style="text-align: left;" data-purpose="layout">Text</p>
<img src="real.jpg" data-mce-src='draft.jpg' alt="Image">
```

EXPECTED: `data-mce-style` and `data-mce-src` disappear; `data-purpose`,
`src="real.jpg"`, `alt`, and text remain. Add an exact name and another `*`
pattern to `remove_attributes` and confirm they match only attribute names.
With `remove_attributes: []`, both TinyMCE attributes remain, including Canvas.

## Test 17: Empty TinyMCE placeholders survive

MODE: all modes, then normal with HTMLPrettify. Saved defaults protect `div`,
`span`, and `i`.

INPUT:

```html
<div></div><span class="icon"></span><i aria-hidden="true"></i>
<strong class="icon">&nbsp;</strong><p>&nbsp;</p><p>Word&nbsp;word</p>
```

EXPECTED: the empty `div`, `span`, and `i` remain and contain NBSP; the existing
`strong` NBSP remains. The blank paragraph is removed, and ordinary prose
becomes `Word word`. NBSP may serialize as Unicode U+00A0. Run twice and confirm
that a second cleanup does not add more NBSPs. Nonempty elements and void
`img` elements must not be padded. Explicit `remove_selectors` still win.

Narrow `protect_empty_selectors` to a class selector and confirm only matching
empty elements are padded. Set it to `[]` and disable
`preserve_nbsp_placeholders` to check the legacy cleanup behavior. Restore the
settings after testing. Finally paste into Moodle TinyMCE, save, reopen, and
inspect learner-facing HTML for preserved elements/classes/ARIA attributes;
record the Moodle/editor version used for this roundtrip.

### Verification — 2026-09-30

PyBuild passed 24 headless regressions and all declared syntax checks. Native
Sublime commands passed a focused TinyMCE fixture in all six modes without
prettify: editor attributes were removed, real image `src` was retained,
empty `div`/`span`/`i` received NBSP, an existing attributed `strong` NBSP was
retained, and the blank paragraph was removed. A custom protection selector
also passed against Sublime's embedded BeautifulSoup. Normal mode with
HTMLPrettify passed on a scratch copy of `testbed.html` plus that fixture.
This does not certify the complete manual plan or a Moodle TinyMCE save/reopen
roundtrip; those broader checks remain separate.
