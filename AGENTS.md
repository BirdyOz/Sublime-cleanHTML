# CleanHTML Project Context

## One-Line Thread Bootstrap

If Greg starts a new thread with:

`Prime yourself from this repo's AGENTS.md and use Tolaria for deeper KB discovery, then briefly confirm and wait for my task.`

treat it as an instruction to:

1. Read this file and the `Start With` sources below.
2. Use the named Tolaria routes for focused discovery; do not load unrelated vault content.
3. Briefly confirm the CleanHTML context, the important defaults, and the available verification path described under `Expected Priming Confirmation`.
4. Name any material source that was unavailable.
5. Make no project changes during priming, then stop and wait for Greg's task.

## Start With

Read only for orientation during priming; do not edit or run the cleaner:

1. `README.md` for scope, supported modes, commands, and package dependencies.
2. `CleanHTML.sublime-settings` for the current configurable defaults.
3. `GB-clean-HTML.py` for implementation details relevant to the next task.
4. `GB-clean-HTML.sublime-commands`, `Default (OSX).sublime-keymap`, and `BirdyOzMenu.sublime-settings` for the exposed Sublime command, keyboard, and shared-menu surfaces.
5. `testplan.md` for expected manual regression cases. Inspect `testbed.html` only when a task needs the runnable fixture or its current state.
6. The central working profile at `/Users/gbird/Dropbox/github/codex-common-core/profiles/working-with-me-profile.md`.

There is currently no project `docs/` directory or automated test harness. Do not infer either one.

## Local Authority

- This repository is authoritative for CleanHTML's current paths, settings, commands, fixtures, implementation, and supported workflow. Project-local facts override central and domain defaults.
- Within the repository, `GB-clean-HTML.py` defines implemented transformations and modes; `CleanHTML.sublime-settings` defines the saved runtime defaults; the command, keymap, and menu files define the exposed Sublime UI.
- `README.md` is the user-facing description of supported behaviour. `testplan.md` records intended manual regression outcomes, and `testbed.html` is a mutable working fixture rather than independent specification.
- If implementation, settings, README, and test expectations disagree, do not silently choose one as intended behaviour. Report the discrepancy and verify in Sublime Text or ask Greg which contract should change.
- Preserve unrelated dirty work. Priming is read-only, and later tasks must not discard user edits in `GB-clean-HTML.py`, `testbed.html`, or any other file.

## Knowledge Routing

Use these Tolaria routes narrowly:

- `CC` / `codex-common-core`: working style, cross-project defaults, prompting, and knowledge routing. Start with the working profile above; use `/Users/gbird/Dropbox/github/codex-common-core/docs/vault-registry.md` when route availability or ownership is unclear.
- `SUB` / `sublime-tooling`: shared Sublime Text package layout, embedded-runtime and dependency constraints, BirdyOz menu conventions, keyboard-first workflows, and in-editor testing. Start with `/Users/gbird/Dropbox/github/sublime-tooling/AGENTS.md`, then follow only the relevant route from its `Start With` list.
- `MOO` / `moodle-content-authoring`: reusable, tool-independent Moodle editor cleanup, content fidelity, transformation, and QA guidance. Start with `/Users/gbird/Dropbox/github/moodle-content-authoring/AGENTS.md` when the task concerns Moodle/ATTO/TinyMCE content semantics rather than Sublime mechanics.

Keep CleanHTML's exact regexes, selectors, modes, settings, commands, fixtures, and known issues in this repository. Promote only reusable cross-plugin Sublime lessons to `SUB`, reusable tool-independent Moodle authoring lessons to `MOO`, and stable cross-project working guidance to `CC`. Current project facts always remain local.

## Project Defaults

- CleanHTML is a Sublime Text command for rewriting whole strict-HTML documents, especially editor-generated Moodle content. Use CleanMD, not this package, for mixed Markdown with embedded HTML.
- Supported modes are `normal`, `deep`, `canvas`, `table`, `mp`, and `mpextended`; `normal` is the command's implementation default.
- Current saved settings enable external-link normalization, nested-paragraph repair, and HTMLPrettify after cleanup. Audio hoisting is disabled. Settings-driven unwrap and removal selectors are part of runtime behaviour.
- The `normal, no prettify` command is the preferred way to inspect structural cleanup before formatting.
- The cleaner operates across the whole document. Use a working copy for tests and preserve the existing command palette, shared BirdyOz menu, and keyboard-first workflow unless a task explicitly changes them.
- Sublime Text's embedded runtime and installed packages are material constraints. HTML-CSS-JS Prettify is required for the normal final formatting path, and BeautifulSoup is used by the plugin's structural cleanup.

## Verification Options

- Treat in-editor execution in Sublime Text as authoritative. Run the relevant command mode on a working copy of `testbed.html` and compare it with `testplan.md`.
- Use `BirdyOz - Clean HTML (normal, no prettify)` to isolate CleanHTML structural output from HTMLPrettify output.
- Match verification to the affected modes and include both transformed content and content that must remain untouched when broadening cleanup rules.
- Test plan case 14 requires `hoist_audio_to_top` to be enabled; it is not the current saved default. State that setup when using the case.
- A Python compile check can catch syntax errors but cannot replace loading the package and exercising it inside Sublime Text. Report any in-editor check that could not be run.

## Expected Priming Confirmation

When every named source and Tolaria route is available, confirm with this exact concise response, then wait:

> Primed for CleanHTML: it rewrites whole strict-HTML documents in Sublime Text; mixed Markdown belongs in CleanMD. Current defaults normalize external links, repair nested paragraphs, and run HTMLPrettify, while audio hoisting is off. I’ll preserve the existing modes and keyboard/menu workflow, and verify changes in Sublime on a working copy against the manual test plan. I consulted the `CC`, `SUB`, and relevant `MOO` routes. No project changes made. Ready for your task.

If `MOO` is not relevant to the anticipated task during generic priming, consulting its routing instructions is sufficient; do not indiscriminately load its content.

## Fallbacks

- If Tolaria is unavailable, read the local vault paths listed under `Knowledge Routing` and say that local filesystem fallback was used.
- If a named file or vault path is unavailable, continue with the remaining local authoritative sources, identify the missing source in the confirmation, and do not imply that it was consulted.
- If both Tolaria and a relevant fallback source are unavailable, state the resulting knowledge gap and wait for Greg's task or direction. Do not compensate by changing the project, inventing defaults, or searching unrelated vaults.
