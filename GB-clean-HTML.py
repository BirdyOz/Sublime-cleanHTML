"""Settings-driven HTML cleanup with one parse and one buffer replacement."""

from copy import deepcopy
import re
import traceback
from urllib.parse import urlsplit

import sublime
import sublime_plugin
import soupsieve
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString


class ConfigurationError(ValueError):
    """A settings error that must be reported before modifying the buffer."""


class StableDoctype(Doctype):
    # BS adds a newline after each doctype on every serialization. Preserve the
    # document's existing whitespace instead of accumulating one per run.
    """Serialize a doctype without adding a fresh trailing newline on every run."""
    SUFFIX = ">"


# This is an engine schema, not a second set of cleanup defaults.
TOP_LEVEL_KEYS = {
    "schema_version", "modes", "run_htmlprettify_after_clean", "output_formatter",
    "text_exclude_selectors", "empty_elements", "rules",
}
# Each action maps to (required fields, optional fields). Adding a new action
# also requires validation here and an implementation branch in apply_rule.
RULE_FIELDS = {
    "remove": ({"selector"}, {"text_equals", "children_selector"}),
    "unwrap": ({"selector"}, {"bare", "only_child", "children_selector"}),
    "unwrap_nested": ({"selector", "children_selector"}, set()),
    "remove_trailing": ({"selector", "children_selector"}, set()),
    "attributes": ({"selector"}, {"remove", "remove_empty", "remove_matching", "set", "flags"}),
    "classes": ({"selector"}, {"remove", "replace", "add"}),
    "styles": ({"selector", "remove"}, set()),
    "query": ({"selector", "attribute", "remove_patterns"}, {"flags"}),
    "regex_attribute": ({"selector", "attribute", "pattern", "replacement"}, {"flags"}),
    "text": ({"selector", "replacement"}, {"find", "pattern", "flags", "scope", "skip_placeholders"}),
    "comments": (set(), {"pattern", "flags"}),
    "comment_lines": (set(), {"pattern", "flags"}),
    "links": ({"selector", "schemes", "target", "rel", "internal_remove"}, set()),
    "move_to_start": ({"selector", "destination", "separator"}, set()),
    "flatten_table": (
        {"selector", "row_selector", "cell_selector", "caption_selector", "cell_separator",
         "row_separator", "plain_header_selector", "plain_header_tag", "unwrap_selectors", "remove_selectors"},
        set(),
    ),
}
COMMON_RULE_FIELDS = {"id", "action", "enabled", "modes"}
REGEX_FLAGS = {"IGNORECASE": re.IGNORECASE, "MULTILINE": re.MULTILINE, "DOTALL": re.DOTALL}


def require(condition, message):
    """Raise a readable settings error when a validation condition is false."""
    if not condition:
        raise ConfigurationError(message)


def string_list(value, path):
    """Validate a list of nonempty strings; path identifies the setting in errors."""
    require(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value),
            path + " must be a list of nonempty strings")


def selector(value, path):
    """Validate CSS selector syntax before any document can be modified."""
    require(isinstance(value, str) and bool(value.strip()), path + " must be a CSS selector")
    try:
        soupsieve.compile(value)
    except Exception as exc:
        raise ConfigurationError("{}: {}".format(path, exc)) from exc


def regex_flags(rule, path):
    """Convert configured flag names into the combined flags used by Python re."""
    flags = rule.get("flags", [])
    string_list(flags, path + ".flags")
    require(all(flag in REGEX_FLAGS for flag in flags), path + ".flags contains an unsupported flag")
    value = 0
    for flag in flags:
        value |= REGEX_FLAGS[flag]
    return value


def compile_pattern(pattern, flags, path, replacement=None):
    """Compile a settings regex and validate any replacement backreferences.

    Return the compiled pattern, or report the settings path on failure."""
    require(isinstance(pattern, str) and bool(pattern), path + " must be a nonempty regex")
    try:
        compiled = re.compile(pattern, flags)
        if replacement is not None:
            compiled.sub(replacement, "")  # Also validates replacement backreferences.
        return compiled
    except (re.error, IndexError) as exc:
        raise ConfigurationError("{}: {}".format(path, exc)) from exc


def name_match(name, pattern):
    # Escaping makes * the only wildcard; this regex is engine plumbing, not cleanup policy.
    """Match an attribute name case-insensitively, with * as the only wildcard."""
    return re.fullmatch(re.escape(pattern).replace(r"\*", ".*"), name, re.IGNORECASE) is not None


def expand_rule_groups(config):
    """Expand human-friendly rule groups into the engine's ordered rule list.

    Each group supplies an action and optional shared defaults. Entries use
    their single dictionary keys as IDs; strings abbreviate selectors, and pairs
    abbreviate text substitutions. Explicit entry fields override defaults.
    The saved group order is mandatory so execution never depends on object
    key ordering. Return a copy, leaving the settings untouched. Legacy flat
    lists are also accepted for individual overrides and existing fixtures.
    """
    config = deepcopy(config)
    if not isinstance(config, dict) or not isinstance(config.get("rules"), dict):
        return config
    grouped = config["rules"]
    require(set(grouped) == {"order", "groups"}, "rules requires order and groups")
    order, groups = grouped["order"], grouped["groups"]
    string_list(order, "rules.order")
    require(isinstance(groups, dict), "rules.groups must be an object")
    require(len(order) == len(set(order)) and set(order) == set(groups),
            "rules.order must name every group exactly once")
    rules = []
    for name in order:
        group = groups[name]
        path = "rules.groups." + name
        require(isinstance(group, dict) and {"action", "entries"} <= set(group)
                and set(group) <= {"action", "defaults", "match", "entries"},
                path + " requires action and entries; optional defaults and match")
        action = group["action"]
        require(isinstance(action, str) and action in RULE_FIELDS, path + ".action is unsupported")
        defaults = group.get("defaults", {})
        require(isinstance(defaults, dict) and not ({"id", "action"} & set(defaults)),
                path + ".defaults must be fields other than id/action")
        required, optional = RULE_FIELDS[action]
        require(set(defaults) <= required | optional | (COMMON_RULE_FIELDS - {"id", "action"}),
                path + ".defaults contains unsupported fields")
        match = group.get("match", "literal")
        require(match in ("literal", "regex") and ("match" not in group or action == "text"),
                path + ".match is literal or regex and applies only to text groups")
        entries = group["entries"]
        require(isinstance(entries, list), path + ".entries must be an ordered list of named entries")
        for index, named_entry in enumerate(entries):
            entry_path = path + ".entries[{}]".format(index)
            require(isinstance(named_entry, dict) and len(named_entry) == 1,
                    entry_path + " must contain exactly one rule ID and its value")
            rule_id, entry = next(iter(named_entry.items()))
            rule = dict(defaults, id=rule_id, action=action)
            if isinstance(entry, str):
                require("selector" in RULE_FIELDS[action][0], path + " cannot use a selector string")
                rule["selector"] = entry
            elif isinstance(entry, list):
                require(action == "text" and len(entry) in (2, 3)
                        and all(isinstance(x, str) for x in entry[:2]),
                        path + " pairs require text action and [find/pattern, replacement, optional options]")
                rule["pattern" if match == "regex" else "find"], rule["replacement"] = entry[:2]
                if len(entry) == 3:
                    options = entry[2]
                    require(isinstance(options, dict) and not ({"id", "action", "find", "pattern", "replacement"} & set(options)),
                            path + " pair options cannot redefine id/action/find/pattern/replacement")
                    rule.update(options)
            else:
                require(isinstance(entry, dict) and not ({"id", "action"} & set(entry)),
                        path + " entries must be selectors, text pairs or field objects without id/action")
                rule.update(entry)
            rules.append(rule)
    config["rules"] = rules
    return config


def prepare_config(config):
    """Validate and copy the settings, then compile each configured regex.

    Check required fields, unique IDs, modes, selectors and action-specific
    values, including disabled rules. Return a prepared copy with internal
    _pattern, _patterns and _matching fields; leave saved settings untouched.
    Invalid configuration raises ConfigurationError before buffer editing."""
    require(isinstance(config, dict), "settings must be an object")
    require(set(config) == TOP_LEVEL_KEYS,
            "settings keys mismatch: missing {}, unknown {}".format(
                sorted(TOP_LEVEL_KEYS - set(config)), sorted(set(config) - TOP_LEVEL_KEYS)))
    config = expand_rule_groups(config)
    require(type(config["schema_version"]) is int and config["schema_version"] == 1,
            "schema_version must be 1")
    string_list(config["modes"], "modes")
    require(bool(config["modes"]), "modes must contain at least one mode")
    require(len(set(config["modes"])) == len(config["modes"]), "modes must be unique")
    require(type(config["run_htmlprettify_after_clean"]) is bool,
            "run_htmlprettify_after_clean must be true or false")
    require(config["output_formatter"] in ("html", "minimal"), "output_formatter must be html or minimal")
    string_list(config["text_exclude_selectors"], "text_exclude_selectors")
    for value in config["text_exclude_selectors"]:
        selector(value, "text_exclude_selectors")
    empty = config["empty_elements"]
    require(isinstance(empty, dict) and set(empty) == {
        "protect_selectors", "remove_selectors", "preserve_nbsp_in_attributed_tags", "preserve_attributes", "padding"
    }, "empty_elements requires protect_selectors, remove_selectors, preserve_nbsp_in_attributed_tags, preserve_attributes, padding")
    for key in ("protect_selectors", "remove_selectors", "preserve_attributes"):
        string_list(empty[key], "empty_elements." + key)
    for key in ("protect_selectors", "remove_selectors"):
        for value in empty[key]:
            selector(value, "empty_elements." + key)
    require(type(empty["preserve_nbsp_in_attributed_tags"]) is bool,
            "empty_elements.preserve_nbsp_in_attributed_tags must be true or false")
    require(isinstance(empty["padding"], str) and bool(empty["padding"]), "empty_elements.padding must be nonempty text")
    require(isinstance(config["rules"], list), "rules must be a list")
    # Validate every rule before executing any; IDs are labels, not action names.
    ids = set()
    for index, rule in enumerate(config["rules"]):
        path = "rules[{}]".format(index)
        require(isinstance(rule, dict), path + " must be an object")
        require(isinstance(rule.get("id"), str) and bool(rule["id"].strip()), path + ".id is required")
        path += " (" + rule["id"] + ")"
        require(rule["id"] not in ids, path + " has a duplicate id")
        ids.add(rule["id"])
        action = rule.get("action")
        require(isinstance(action, str) and action in RULE_FIELDS, path + " has an unsupported action")
        required, optional = RULE_FIELDS[action]
        require(required <= set(rule), path + " missing " + str(sorted(required - set(rule))))
        require(set(rule) <= required | optional | COMMON_RULE_FIELDS,
                path + " unknown keys " + str(sorted(set(rule) - required - optional - COMMON_RULE_FIELDS)))
        if "enabled" in rule:
            require(type(rule["enabled"]) is bool, path + ".enabled must be true or false")
        if "modes" in rule:
            string_list(rule["modes"], path + ".modes")
            require(set(rule["modes"]) <= set(config["modes"]), path + ".modes contains an unknown mode")
        for key in ("selector", "children_selector", "row_selector", "cell_selector", "caption_selector", "plain_header_selector", "destination"):
            if key in rule:
                selector(rule[key], path + "." + key)
        for key in ("bare", "only_child", "skip_placeholders"):
            if key in rule:
                require(type(rule[key]) is bool, path + "." + key + " must be true or false")
        for key in ("attribute", "replacement", "find", "target", "cell_separator", "row_separator", "text_equals"):
            if key in rule:
                require(isinstance(rule[key], str), path + "." + key + " must be text")
        if action == "text":
            require(("find" in rule) != ("pattern" in rule), path + " requires exactly one of find or pattern")
            require(rule.get("scope", "all") in ("all", "leading"), path + ".scope must be all or leading")
            if "find" in rule:
                require(bool(rule["find"]), path + ".find cannot be empty")
        if action in ("attributes", "classes"):
            for key in ("remove", "remove_empty", "add"):
                if key in rule:
                    string_list(rule[key], path + "." + key)
            for key in ("set", "replace", "remove_matching"):
                if key in rule:
                    require(isinstance(rule[key], dict), path + "." + key + " must be an object")
                    for name, value in rule[key].items():
                        require(isinstance(name, str) and bool(name), path + " has an empty name")
                        require(isinstance(value, str), path + "." + key + " values must be text")
        if action == "styles":
            require(isinstance(rule["remove"], dict), path + ".remove must map CSS properties to value lists")
            for name, values in rule["remove"].items():
                require(isinstance(name, str) and bool(name), path + " has an empty property")
                string_list(values, path + ".remove." + name)
        if action == "links":
            for key in ("schemes", "rel", "internal_remove"):
                string_list(rule[key], path + "." + key)
        if action == "flatten_table":
            validate_tag_name(rule["plain_header_tag"], path + ".plain_header_tag")
            for key in ("unwrap_selectors", "remove_selectors"):
                string_list(rule[key], path + "." + key)
                for value in rule[key]:
                    selector(value, path + "." + key)
        if action == "move_to_start":
            sep = rule["separator"]
            require(isinstance(sep, dict) and set(sep) == {"tag", "attributes"}, path + ".separator requires tag and attributes")
            validate_tag_name(sep["tag"], path + ".separator.tag")
            require(isinstance(sep["attributes"], dict), path + ".separator.attributes must be an object")
            for name, value in sep["attributes"].items():
                require(isinstance(name, str) and bool(name) and isinstance(value, (str, list)), path + " has invalid separator attributes")
                if isinstance(value, list):
                    string_list(value, path + ".separator.attributes." + name)
        # Cache compiled patterns only in this copied runtime configuration.
        flags = regex_flags(rule, path)
        if "pattern" in rule:
            rule["_pattern"] = compile_pattern(rule["pattern"], flags, path + ".pattern", rule.get("replacement"))
        if "remove_patterns" in rule:
            string_list(rule["remove_patterns"], path + ".remove_patterns")
            rule["_patterns"] = [compile_pattern(x, flags, path + ".remove_patterns") for x in rule["remove_patterns"]]
        if "remove_matching" in rule:
            rule["_matching"] = {key: compile_pattern(value, flags, path + ".remove_matching." + key)
                                  for key, value in rule["remove_matching"].items()}
    return config


def validate_tag_name(name, path):
    """Validate a tag name used when creating a heading or separator element."""
    require(isinstance(name, str) and bool(name) and name[0].isalpha()
            and all(ch.isalnum() or ch in "-_" for ch in name), path + " must be an HTML tag name")


def load_cleanhtml_settings():
    """Load the current Sublime settings object, including Sublime overrides."""
    return sublime.load_settings("CleanHTML.sublime-settings")


def get_cleanhtml_config(overrides=None):
    """Read the settings into a dictionary without supplying cleanup defaults.

    Optional overrides replace top-level values, primarily for verification.
    Validation is deferred to prepare_config; missing settings must fail
    rather than silently enable a second set of cleanup policy."""
    settings = load_cleanhtml_settings()
    # Missing values intentionally remain None and fail validation; no duplicated policy.
    config = settings.to_dict() if hasattr(settings, "to_dict") else {key: settings.get(key) for key in TOP_LEVEL_KEYS}
    if overrides:
        config.update(overrides)
    return expand_rule_groups(config)


def matches_any(tag, selectors):
    """Return whether this element matches at least one configured CSS selector."""
    return any(soupsieve.match(value, tag) for value in selectors)


def is_excluded(tag, config):
    """Check the element and its ancestors against the text exclusion selectors.

    This also protects descendants inside preformatted or raw-text elements."""
    while tag is not None and getattr(tag, "name", None) is not None:
        if matches_any(tag, config["text_exclude_selectors"]):
            return True
        tag = tag.parent
    return False


def is_empty(tag):
    """Return whether an element has neither child elements nor non-whitespace text."""
    return not tag.find(True) and not tag.get_text(strip=True)


def preserve_empty(tag, config):
    """Decide whether the settings protect an empty element from removal.

    Protection can come from its selector, a meaningful attribute, or an
    existing attributed padding placeholder. Nonempty elements return false."""
    if not is_empty(tag):
        return False
    policy = config["empty_elements"]
    return (matches_any(tag, policy["protect_selectors"])
            or any(name_match(name, pattern) for name in tag.attrs for pattern in policy["preserve_attributes"])
            or (policy["preserve_nbsp_in_attributed_tags"] and bool(tag.attrs)
                and policy["padding"] in tag.get_text()))


def element_children(tag):
    """Return direct child elements, ignoring text, comments and doctypes."""
    return [child for child in tag.children if getattr(child, "name", None) is not None]


def only_tag_children(tag, value):
    """Check for matching child elements with no other meaningful direct content.

    Whitespace and comments are allowed; at least one child element is required."""
    children = element_children(tag)
    return bool(children) and all(soupsieve.match(value, child) for child in children) and all(
        getattr(child, "name", None) is not None or isinstance(child, Comment) or not str(child).strip()
        for child in tag.children)


def split_css(value, delimiter):
    """Split CSS on a delimiter outside quotes, comments and brackets.

    Preserve the original fragments so unfamiliar CSS is retained verbatim.
    This is a conservative scanner, not a full CSS parser."""
    parts, start, depth, quote, escaped, comment = [], 0, 0, None, False, False
    index = 0
    while index < len(value):
        ch = value[index]
        if comment:
            if value[index:index + 2] == "*/":
                comment = False
                index += 1
        elif escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif value[index:index + 2] == "/*":
            comment = True
            index += 1
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == delimiter and depth == 0:
            parts.append(value[start:index])
            start = index + 1
        index += 1
    parts.append(value[start:])
    return parts


def apply_rule(soup, rule, config):
    """Apply one prepared settings rule to the BeautifulSoup tree in place.

    Dispatch by action: delete/unwrap tags, edit attributes/classes/styles,
    replace scoped text or URL values, normalize links, move elements, or
    flatten tables. Return a count of changes for logging; counts describe
    action-specific operations, not necessarily the number of edited tags.
    Text and structural actions respect exclusions where indicated below;
    explicit removal and selected attribute edits may still affect those tags."""
    action = rule["action"]
    changes = 0
    if action == "comment_lines":
        # Mark structural comments with real text-node line boundaries before
        # serialization. HTMLPrettify preserves these existing newlines.
        for node in list(soup.find_all(string=lambda x: isinstance(x, Comment))):
            if is_excluded(node.parent, config) or ("_pattern" in rule and not rule["_pattern"].search(str(node))):
                continue
            for before in (True, False):
                sibling = node.previous_sibling if before else node.next_sibling
                if sibling is None and node.parent is soup:
                    continue  # No adjacent markup at a document boundary.
                if isinstance(sibling, NavigableString) and not isinstance(sibling, (Comment, Doctype)):
                    if not str(sibling).strip():
                        if "\n" not in str(sibling):
                            sibling.replace_with(NavigableString("\n"))
                            changes += 1
                        continue
                if before:
                    node.insert_before(NavigableString("\n"))
                else:
                    node.insert_after(NavigableString("\n"))
                changes += 1
        return changes
    if action == "comments":
        for node in list(soup.find_all(string=lambda x: isinstance(x, Comment))):
            if not is_excluded(node.parent, config) and ("_pattern" not in rule or rule["_pattern"].search(str(node))):
                node.extract()
                changes += 1
        return changes
    tags = list(soup.select(rule["selector"]))
    if action in ("unwrap", "unwrap_nested", "flatten_table"):
        tags.reverse()  # Descendants first; newly empty parents are handled later.
    if action == "text":
        # Structural edits can leave adjacent strings. Match the same text nodes
        # that a subsequent HTML parse would see, without reparsing the document.
        soup.smooth()
        # Overlapping selectors may expose the same text node more than once.
        # Process it once per rule so replacements cannot accidentally cascade.
        seen = set()
        visited = []  # Keep identity references alive while matching nested selectors.
        for tag in tags:
            nodes = [node for node in tag.descendants if isinstance(node, NavigableString) and not isinstance(node, (Comment, Doctype))]
            if rule.get("scope", "all") == "leading":
                nodes = next(([node] for node in nodes if str(node).strip()), [])
            for node in nodes:
                if id(node) in seen or node.parent is None or is_excluded(node.parent, config):
                    continue
                seen.add(id(node))
                visited.append(node)
                if rule.get("skip_placeholders", False) and preserve_empty(node.parent, config):
                    continue
                old = str(node)
                if "_pattern" in rule:
                    new, count = rule["_pattern"].subn(rule["replacement"], old)
                else:
                    count = old.count(rule["find"])
                    new = old.replace(rule["find"], rule["replacement"])
                if new != old:
                    replacement = NavigableString(new)
                    node.replace_with(replacement)
                    seen.add(id(replacement))
                    visited.append(replacement)
                    changes += count
        return changes
    if action == "move_to_start":
        if not tags:
            return 0
        destination = soup.select_one(rule["destination"]) or soup
        leading = element_children(destination)[:len(tags)]
        if [id(x) for x in leading] == [id(x) for x in tags]:
            return 0
        for tag in tags:
            # Never move an ancestor into its descendant.
            require(destination is not tag and destination not in tag.descendants,
                    rule["id"] + " destination is inside a selected element")
            tag.extract()
        separator = soup.new_tag(rule["separator"]["tag"], attrs=deepcopy(rule["separator"]["attributes"]))
        offset = 1 if destination.contents and isinstance(destination.contents[0], Doctype) else 0
        for index, tag in enumerate(tags + [separator]):
            destination.insert(offset + index, tag)
        return len(tags)
    for tag in tags:
        if tag.parent is None:
            continue
        if action == "remove":
            # A child selector lets settings delete wrapper-only artifacts
            # without deleting paragraphs that also contain meaningful text.
            if "children_selector" in rule and not only_tag_children(tag, rule["children_selector"]):
                continue
            if "text_equals" not in rule or tag.get_text() == rule["text_equals"]:
                tag.decompose()
                changes += 1
        elif action in ("unwrap", "unwrap_nested"):
            if is_excluded(tag, config) or preserve_empty(tag, config):
                continue
            if rule.get("bare", False) and tag.attrs:
                continue
            if rule.get("only_child", False) and (element_children(tag.parent) != [tag] or any(
                    not isinstance(child, Comment) and getattr(child, "name", None) is None and str(child).strip()
                    for child in tag.parent.children)):
                continue
            if "children_selector" in rule and not only_tag_children(tag, rule["children_selector"]):
                continue
            tag.unwrap()
            changes += 1
        elif action == "remove_trailing":
            if is_excluded(tag, config):
                continue
            for child in list(tag.contents)[::-1]:
                if isinstance(child, Comment) or (getattr(child, "name", None) is None and not str(child).strip()):
                    continue
                if getattr(child, "name", None) and soupsieve.match(rule["children_selector"], child):
                    child.decompose()
                    changes += 1
                else:
                    break
        elif action == "attributes":
            for name in list(tag.attrs):
                value = tag.attrs[name]
                text = " ".join(value) if isinstance(value, list) else str(value)
                if (any(name_match(name, pattern) for pattern in rule.get("remove", []))
                        or (name in rule.get("remove_empty", []) and not text.strip())
                        or (name in rule.get("_matching", {}) and rule["_matching"][name].fullmatch(text))):
                    del tag.attrs[name]
                    changes += 1
            for name, value in rule.get("set", {}).items():
                if tag.get(name) != value:
                    tag[name] = value
                    changes += 1
        elif action == "classes":
            # Class names are tokens: never replace substrings of another class.
            old = list(tag.get("class", []))
            new = []
            for value in old:
                if value not in rule.get("remove", []):
                    value = rule.get("replace", {}).get(value, value)
                    if value and value not in new:
                        new.append(value)
            for value in rule.get("add", []):
                if value not in new:
                    new.append(value)
            if new != old:
                if new:
                    tag["class"] = new
                else:
                    tag.attrs.pop("class", None)
                changes += 1
        elif action == "styles":
            old = tag.get("style", "")
            if not isinstance(old, str):
                continue
            # Remove exact property/value pairs, keeping other CSS fragments.
            kept = []
            removed = 0
            policy = {key.casefold(): [x.strip().casefold() for x in values] for key, values in rule["remove"].items()}
            for declaration in split_css(old, ";"):
                pieces = split_css(declaration, ":")
                if len(pieces) >= 2 and ":".join(pieces[1:]).strip().casefold() in policy.get(pieces[0].strip().casefold(), []):
                    removed += 1
                else:
                    kept.append(declaration)
            if removed:
                new = ";".join(kept).strip()
                if not new.strip("; "):
                    tag.attrs.pop("style", None)
                else:
                    tag["style"] = new
                changes += removed
        elif action in ("query", "regex_attribute"):
            old = tag.get(rule["attribute"])
            if not isinstance(old, str):
                continue
            if action == "regex_attribute":
                new, count = rule["_pattern"].subn(rule["replacement"], old)
            else:
                # Preserve untouched URL spelling; decoding/re-encoding could
                # alter signed URLs, escapes or unrelated query parameters.
                before_fragment, marker, fragment = old.partition("#")
                path, query_marker, query = before_fragment.partition("?")
                if not query_marker:
                    continue
                items = query.split("&")
                kept = [item for item in items if not any(pattern.fullmatch(item) for pattern in rule["_patterns"])]
                count = len(items) - len(kept)
                new = path + (("?" + "&".join(kept)) if kept else "") + marker + fragment
            if new != old:
                tag[rule["attribute"]] = new
                changes += count
        elif action == "links":
            try:
                external = urlsplit(tag.get("href", "")).scheme.lower() in rule["schemes"]
            except ValueError:
                continue  # Preserve malformed URLs rather than guessing.
            if external:
                # Merge safety tokens rather than discarding existing rel values.
                if tag.get("target") != rule["target"]:
                    tag["target"] = rule["target"]
                    changes += 1
                old = tag.get("rel", [])
                old = old.split() if isinstance(old, str) else list(old)
                new = old + [value for value in rule["rel"] if value not in old]
                if new != old:
                    tag["rel"] = new
                    changes += 1
            else:
                for name in rule["internal_remove"]:
                    if name in tag.attrs:
                        del tag.attrs[name]
                        changes += 1
        elif action == "flatten_table":
            changes += flatten_table(soup, tag, rule)
    return changes


def flatten_table(soup, table, rule):
    """Remove table markup while preserving cell contents and configured boundaries.

    Insert cell/row separators, wrap nonempty plain-text headers in the
    configured heading tag, delete configured column markup, then unwrap
    descendants before their parents. Formatted headers keep their inner HTML.
    Return the number of removed or unwrapped elements for rule logging."""
    changes = 0
    rows = list(table.select(rule["row_selector"]))
    captions = list(table.select(rule["caption_selector"]))
    for caption in captions:
        if rows:
            caption.insert_after(NavigableString(rule["row_separator"]))
    # Separators keep neighboring cells from becoming a single word when
    # their wrappers disappear. Header conversion keeps the original text nodes.
    for index, row in enumerate(rows):
        if index:
            row.insert_before(NavigableString(rule["row_separator"]))
        cells = list(row.select(rule["cell_selector"]))
        for cell_index, cell in enumerate(cells):
            if cell_index:
                cell.insert_before(NavigableString(rule["cell_separator"]))
            if soupsieve.match(rule["plain_header_selector"], cell) and not cell.find(True) and cell.get_text(strip=True):
                heading = soup.new_tag(rule["plain_header_tag"])
                for child in list(cell.contents):
                    heading.append(child.extract())
                cell.append(heading)
    for value in rule["remove_selectors"]:
        for node in list(table.select(value)):
            if node.parent is not None:
                node.decompose()
                changes += 1
    # Preserve unfamiliar inner HTML too; only configured table tags are unwrapped.
    wrappers = [node for node in table.find_all(True) if matches_any(node, rule["unwrap_selectors"])]
    for node in reversed(wrappers):
        if node.parent is not None:
            node.unwrap()
            changes += 1
    table.unwrap()
    return changes + 1


def finalize_empty_elements(soup, config):
    """Pad protected empty elements and remove configured disposable empty tags.

    Work from descendants to ancestors so deleting a child can expose an
    empty parent in the same pass. Excluded and HTML void elements are kept.
    Return the number of padding insertions and element deletions."""
    changes = 0
    policy = config["empty_elements"]
    for tag in reversed(list(soup.find_all(True))):
        if tag.parent is None or is_excluded(tag, config) or tag.is_empty_element or not is_empty(tag):
            continue
        if preserve_empty(tag, config):
            if policy["padding"] not in tag.get_text():
                tag.append(policy["padding"])
                changes += 1
        elif matches_any(tag, policy["remove_selectors"]):
            tag.decompose()
            changes += 1
    return changes


def clean_html(source, mode, config):
    """Clean an HTML string and return (serialized_html, per_rule_change_counts).

    Validate first, parse once, run explicit removals before other rules,
    protect empty elements before unwrapping, and finalize empties afterward.
    Serialize once with the configured formatter. This function has no
    Sublime buffer side effects; errors propagate to the command adapter."""
    config = prepare_config(config)
    require(mode in config["modes"], "unknown or retired cleaning mode: " + str(mode))
    soup = BeautifulSoup(source, "html.parser")
    counts = {}
    active = [rule for rule in config["rules"] if rule.get("enabled", True) and mode in rule.get("modes", config["modes"])]
    # Explicit removals always win, even when listed after an unwrap in settings.
    prepared_empty = False
    for rule in [x for x in active if x["action"] == "remove"] + [x for x in active if x["action"] != "remove"]:
        # Pad newly empty protected wrappers before an unwrap can erase them.
        if not prepared_empty and rule["action"] in ("unwrap", "unwrap_nested", "flatten_table"):
            count = finalize_empty_elements(soup, config)
            if count:
                counts["empty-elements"] = count
            prepared_empty = True
        count = apply_rule(soup, rule, config)
        if count:
            counts[rule["id"]] = count
    count = finalize_empty_elements(soup, config)
    if count:
        counts["empty-elements"] = counts.get("empty-elements", 0) + count
    for node in list(soup.find_all(string=lambda value: isinstance(value, Doctype))):
        node.replace_with(StableDoctype(str(node)))
    return soup.decode(formatter=config["output_formatter"]), counts


class CleanHtml(sublime_plugin.TextCommand):
    """Expose the settings-driven cleaner as Sublime’s clean_html text command."""
    def run(self, edit, **kwargs):
        """Clean the whole buffer, preserving selections and optionally requesting prettify.

        Command argument type selects the mode; otherwise use the first saved
        mode. no_prettify skips final formatting for this invocation. Compute
        and validate all structural output before editing, replace at most
        once, then report per-rule counts. Errors leave the buffer unchanged."""
        mode = kwargs.get("type")
        try:
            config = get_cleanhtml_config()
            if mode is None:
                require(isinstance(config.get("modes"), list) and bool(config["modes"]), "modes must contain at least one mode")
                mode = config["modes"][0]
            region = sublime.Region(0, self.view.size())
            original = self.view.substr(region)
            output, counts = clean_html(original, mode, config)
        except ConfigurationError as exc:
            message = "CleanHTML: " + str(exc)
            print(message)
            sublime.status_message(message)
            return
        except Exception:
            traceback.print_exc()
            sublime.status_message("CleanHTML: cleanup failed; document unchanged (see console)")
            return
        # This is the first point where editing is allowed: cleanup succeeded.
        changed = output != original
        if changed:
            # Preserve selection direction and clamp endpoints to the new size;
            # these are positional bounds, not a semantic cursor remapping.
            selections = [(region.a, region.b) for region in self.view.sel()]
            self.view.replace(edit, region, output)
            self.view.sel().clear()
            for start, end in selections:
                self.view.sel().add(sublime.Region(min(start, len(output)), min(end, len(output))))
        summary = "CleanHTML ({}): {} changes across {} rules{}".format(
            mode, sum(counts.values()), len(counts), "" if changed else ", document unchanged")
        if config["run_htmlprettify_after_clean"] and not kwargs.get("no_prettify", False):
            self.view.run_command("htmlprettify")
            summary += ", prettify requested"
        else:
            summary += ", prettify skipped"
        print(summary)
        if counts:
            print("CleanHTML rules: " + ", ".join("{}={}".format(key, value) for key, value in counts.items()))
        self.view.set_status("CleanHTML summary", summary)
        # A prior run's timeout must not clear the status for a more recent run.
        token = object()
        self._summary_token = token
        def clear_status():
            """Clear this run’s summary only if a newer run has not replaced it."""
            if self._summary_token is token:
                self.view.erase_status("CleanHTML summary")
        sublime.set_timeout(clear_status, 8000)
