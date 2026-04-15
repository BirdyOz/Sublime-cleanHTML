# CleanHTML Test Plan

This file records representative manual regression cases for `GB-clean-HTML.py`.

Each case includes:

- `MODE`: the command mode to run (`normal`, `deep`, `table`, `canvas`, `mp`, or `mpextended`)
- `INPUT`: sample source HTML
- `EXPECTED`: the intended result after running `CleanHTML`

These examples are designed as a review checklist rather than an executable test harness.

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
