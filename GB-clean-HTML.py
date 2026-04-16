import re

import sublime
import sublime_plugin
from bs4 import BeautifulSoup

DEFAULT_CLEANHTML_CONFIG = {
    "normalize_external_links": True,
    "repair_nested_paragraph_wrappers": True,
    "hoist_audio_to_top": True,
    "run_htmlprettify_after_clean": True,
    "unwrap_selectors": [
        "section",
        "article",
        "a[name]",
        "li > p",
    ],
    "remove_selectors": [
        'a[href*="readspeaker.com"]',
        'img[src*="readspeaker.com"]',
    ],
}

VALID_CLEANHTML_TYPES = {"normal", "deep", "canvas", "table", "mp", "mpextended"}

def load_cleanhtml_settings():
    return sublime.load_settings("CleanHTML.sublime-settings")

def get_cleanhtml_config(overrides=None):
    settings = load_cleanhtml_settings()
    unwrap_selectors = settings.get(
        "unwrap_selectors",
        DEFAULT_CLEANHTML_CONFIG["unwrap_selectors"],
    )
    remove_selectors = settings.get(
        "remove_selectors",
        DEFAULT_CLEANHTML_CONFIG["remove_selectors"],
    )
    config = {
        "normalize_external_links": settings.get(
            "normalize_external_links",
            DEFAULT_CLEANHTML_CONFIG["normalize_external_links"],
        ),
        "repair_nested_paragraph_wrappers": settings.get(
            "repair_nested_paragraph_wrappers",
            DEFAULT_CLEANHTML_CONFIG["repair_nested_paragraph_wrappers"],
        ),
        "hoist_audio_to_top": settings.get(
            "hoist_audio_to_top",
            DEFAULT_CLEANHTML_CONFIG["hoist_audio_to_top"],
        ),
        "run_htmlprettify_after_clean": settings.get(
            "run_htmlprettify_after_clean",
            DEFAULT_CLEANHTML_CONFIG["run_htmlprettify_after_clean"],
        ),
        "unwrap_selectors": list(unwrap_selectors) if isinstance(unwrap_selectors, list) else list(DEFAULT_CLEANHTML_CONFIG["unwrap_selectors"]),
        "remove_selectors": list(remove_selectors) if isinstance(remove_selectors, list) else list(DEFAULT_CLEANHTML_CONFIG["remove_selectors"]),
    }

    if isinstance(overrides, dict):
        config.update(overrides)

    return config

def normalize_external_links(string):
    """Add safe target/rel attributes to external links without reparsing the full document."""
    def normalize_anchor_open_tag(match):
        open_tag = match.group(0)
        soup = BeautifulSoup(open_tag + "</a>", "html.parser")
        tag = soup.find("a")
        if tag is None:
            return open_tag

        href = tag.get("href", "")
        if not isinstance(href, str):
            href = ""
        if tag.has_attr("target"):
            del tag["target"]
        if tag.has_attr("rel"):
            del tag["rel"]
        if re.match(r"^https?://", href, flags=re.IGNORECASE):
            tag["target"] = "_blank"
            tag["rel"] = "noopener noreferrer"

        serialised = str(tag)
        if serialised.endswith("</a>"):
            return serialised[:-4]
        return open_tag

    return re.sub(r"<a\b[^>]*?>", normalize_anchor_open_tag, string, flags=re.IGNORECASE | re.DOTALL)

def repair_nested_paragraph_wrappers(string):
    """Unwrap invalid outer <p> tags that contain only nested block <p> tags."""
    soup = BeautifulSoup(string, "html.parser")

    changed = True
    while changed:
        changed = False
        for p_tag in soup.find_all("p"):
            child_tags = [child for child in p_tag.children if getattr(child, "name", None) is not None]
            if not child_tags:
                continue

            only_nested_p = True
            for child in p_tag.children:
                name = getattr(child, "name", None)
                if name is None:
                    if str(child).strip():
                        only_nested_p = False
                        break
                    continue
                if name != "p":
                    only_nested_p = False
                    break

            if only_nested_p:
                p_tag.unwrap()
                changed = True
                break

    return str(soup)

def apply_selector_unwraps(soup, selectors):
    count = 0
    for selector in selectors:
        if not isinstance(selector, str) or not selector.strip():
            continue
        try:
            matches = list(soup.select(selector))
        except Exception as exc:
            print("CleanHTML: invalid unwrap selector '{}': {}".format(selector, exc))
            continue
        for tag in matches:
            if getattr(tag, "parent", None) is None:
                continue
            if selector == "div:not([class]):not([id]):not([style])" and getattr(tag, "attrs", None):
                continue
            tag.unwrap()
            count += 1
    return count

def apply_selector_removals(soup, selectors):
    count = 0
    for selector in selectors:
        if not isinstance(selector, str) or not selector.strip():
            continue
        try:
            matches = list(soup.select(selector))
        except Exception as exc:
            print("CleanHTML: invalid remove selector '{}': {}".format(selector, exc))
            continue
        for tag in matches:
            if getattr(tag, "parent", None) is None:
                continue
            tag.decompose()
            count += 1
    return count

def unwrap_inline_heading_wrappers(soup):
    count = 0
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        for child in heading.find_all(["strong", "b", "em", "i"]):
            if child.has_attr("aria-hidden") and str(child.get("aria-hidden")).lower() == "true":
                continue
            if child.name == "i":
                continue
            child.unwrap()
            count += 1
    return count

def remove_empty_known_tags(soup):
    count = 0
    empty_tag_names = ["p", "strong", "em", "li", "b", "ol", "ul", "h1", "h2", "h3", "h4", "h5", "h6"]
    for tag in soup.find_all(empty_tag_names):
        if not tag.get_text(strip=True) and not tag.find(True):
            tag.decompose()
            count += 1
    return count

def unwrap_table_tags(soup):
    count = 0
    for tag in soup.find_all(["table", "tbody", "tr", "th", "thead", "td", "caption"]):
        tag.unwrap()
        count += 1
    return count

def clean_html_structure(string, mode, config):
    """Apply tree-based structural cleanup and return text plus removal count."""
    soup = BeautifulSoup(string, "html.parser")
    tags_removed = 0

    tags_removed += apply_selector_unwraps(soup, config.get("unwrap_selectors", []))
    tags_removed += apply_selector_removals(soup, config.get("remove_selectors", []))
    tags_removed += unwrap_inline_heading_wrappers(soup)
    tags_removed += remove_empty_known_tags(soup)

    if mode == "table":
        tags_removed += unwrap_table_tags(soup)

    return str(soup), tags_removed

class CleanHtml(sublime_plugin.TextCommand):
    # Type = normal - Remove spans, font-sizes, non-breaking spaces empty tags etc.
    # Type = deep - Normal + style attributes
    # Type = table - Deep plus table tags

    def run(self, edit, **kwargs):
        type = kwargs.get("type", "normal")
        no_prettify = bool(kwargs.get("no_prettify", False))

        if type not in VALID_CLEANHTML_TYPES:
            message = "CleanHTML: unknown cleaning mode '{}'".format(type)
            print(message)
            sublime.status_message(message)
            return

        config = get_cleanhtml_config()
        if no_prettify:
            config["run_htmlprettify_after_clean"] = False

        # Update status image
        status_msg = "Clean HTML = " + type + " cleaning"
        self.view.set_status("cleaning",status_msg)
        sublime.set_timeout(lambda: self.view.erase_status("cleaning"), 8000)

                                                                             # NORMAL SUBSTITUTIONS
        substitutions = [                                                    # ====================
        ('&nbsp;', ' '),                                                     # Non breaking spaces
        (' style *= *\"font-size: 1rem;.*?\"', ''),                          # font-sizes
        (' id *= *\"yui.*?\"', ''),                                          # yui id's
        (' dir=\"ltr\"', ''),                                                # redundant LTR declarations
        (' style=\"text-align: left;\"', ''),                                # redundant text aligns
        ('(<li>)[ \\#\\*•·-]+', '\\1'),                                        # li's that start with •,#,* etc.
        ('(<li>)[1-9]+\\. *', '\\1'),                                         # li's that start with a number
        ('(<[^>]*class=\"[^>]*)(Bodycopyindented|rspkr_dr_added) *', '\\1'), # specific classes
        ('(<[^>]*)(class|id|style)=\" *\"','\\1'),                           # specific empty attributes
        (' dir="ltr" style="text-align: left;"',''),                         # Get rid of ATTO's default para style on blank pages
        ('<p><br></p>','<br>'),                                              # p's that only contain br
        ('<br>\\w?</p>','</p>'),                                              # br just before a closing p
        ('<\\!-- ?\\[(if|end).*?-->',''),                                      # MSWord style comments
        ('(<img[^>]+)\\?time=\\d{13,}','\\1'),                               # images with time stamps.  Prevents Moodle errors
        # ('(<img[^>]+)width="\d+\%?" height="\d+\%?" ','\\1'),              # remove image dimensions
        ('http://127.0.0.1.*?\\#','#'),                                       # remove localhost prefix
        (' atto_image_button_text-bottom',' w-100'),                         # remove img classes added by the ATTO editor
        ('\\?*time\\d{8,}', ''),                                             # Remove Moodle timestamps from image src
        ('(?<=<td)(?<!>) width="\\d+\\%?"',''),                                # remove <td> widths
        (' valign="top"',''),                                                # remove <td> valign="top"
        ('<br>',''),                                                         # Momentarily delete target="_blank"
        ('<a class="source-btn" data-toggle="collapse" href="#show',         # Specific cleanup of attribution helpers
        '<a class="source-btn text-muted" data-toggle="collapse" href="#show'),
        ('▼ Show attribution', '▽ Show attribution'),
        ('<div style="display: block;" class="ghost-text-message">Connected! You can switch to your editor</div>','')
        ]
                                                                             # ADD BACK IN WHITESPACE
        linebreaks = [                                                       # ======================
        ('(<!--|<br>|<img|<small)', '\\n\\1'),                               # breaks before certain tags
        ('(<hr>)', '\\n\\n\\n\\1\\n\\n\\n'),                                 # Extra lines before and after HR's
        ('(<!-- Start [^>]*-->)', '\\n\\1'),                                 # Extra line before Start of comment block
        ('(<!-- End [^>]*-->)', '\\1\\n\\n')                                 # Extra after end of comment block
        ]

        # ALTERNATIVE SUBSTITUTIONS
        # =========================
                                                                             # DEEP SUBSTITUTIONS
        deepsubs = [                                                         # ==================
        (' \\[OPTIONAL\\] ',' ')                                               # Remove all style attributes
        # (' style=\".*?\"',''),                                               # Remove all style attributes
        # (' [^a][\w-]+=" *"(?=.*?>)','')                                      # Remove empty attributes that are not alt
        ]
                                                                             # CANVASLMS SUBSTITUTIONS
        canvassubs = [                                                       # ==================
        ('data-mce-.*?".*?" ?', ''),                                         # Canvas MCE editor
        (' target="_blank"',''),                                             # Delete all target="_blank"
        ('<!--.*?-->',''),                                                   # Delete all comments
        ('<br>',''),                                                         # Delete <br>
        (' data-mce-style=".*?"',''),                                        # Delete data attributes
        ('9864','9948'),('9865','9949'),('9866','9947'),('9867','9946'),('9868','9945'),('9869','9944'),('9870','9943'),('9871','9942'),('9872','9941'),('9873','9940')
        ]
                                                                             # MELB POLY SUBSTITUTIONS
        mpsubs = [                                                           # ==================
        ('<p class="(bulletlist|standardbulletpoint)".*?>(.*?)</p>','<li>\\2</li>'), # Convert p bullets into li
        ('(( <li>.*?</li>)+)','<ul>\\1</ul>'),                               # Wrap converted list groups in ul
        ('<span.*?>',''),                                                    # All open spans
        ('</span.*?>',''),                                                   # All closed spans
        ('<p[^>]*>\n*(<img.*?>)</p>', '\\1'),                                # Remove p tags around images (to avoid confusion with other paras)


        # All images - Float images right
        ('<img src="(.*?)" longdesc="(.*?)".*?(<a.*?)</p>', '<figure class="figure border rounded p-1 bg-light text-right float-right ml-4 col-5 w-100"> <img class="w-100" src="\\1" alt="\\2"> <figcaption class="figure-caption text-muted small fw-lighter"> <small> \\3 </small> </figcaption> </figure>'),
        # If I am an image in a table, reset to w-100
        ('float-right ml-4 col-5(?=.*?</td>)',''),
        # Learning activities
        ('<table class="TableGrid".*?<p class="learningactivity">.*?<td class="TableGrid">(.*?)</td>.*?</table>', '<div class="clearfix container-fluid"></div> <div class="card mt-1 mb-1"> <div class="card-body"> <h4 class="card-title text-danger"><i aria-hidden="true" class="fa fa-tasks"></i> Learning Activity</h4> \\1 </div> </div>'),
        # Youtube video
        (r'<p class="weblink">(Weblink:|)*(.*?)</p> <p><a href="https://(youtu\.be/|www\.youtube\.com/watch\?v=)(.*?)".*?</p>', '<div class="clearfix container-fluid"></div> <div class="card mt-1 mb-1"> <div class="card-body"> <h4 class="text-danger yt-title"><i class="fa fa-play-circle-o"></i> \\2</h4> <div class="embed-responsive embed-responsive-16by9"> <iframe id="yt-placeholder" class="embed-responsive-item vjs-tech" frameborder="0" allowfullscreen="1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" title="\\2" width="100%" height="100%" src="https://www.youtube.com/embed/\\4?modestbranding=1&amp;rel=0&amp;enablejsapi=1&amp;origin=https%3A%2F%2Fbirdyoz.github.io&amp;widgetid=1" data-gtm-yt-inspected-4="true"></iframe> </div> </div> </div>'),
        # Weblinks #TODO - Remove alert.   Collapse to one line
        ('<p class="weblink">(Weblink:|)*(.*?)</p> <p><a href="(http.*?)".*?</p>','<p>Weblink: <strong><a href="\\3" target="_blank">\\2</a></strong></p>'),
        # Remove .weblink to prevent double processsing MS Word links and YT vids
        (' class="weblink"',''),
        # Swap MSWord Table styles for Bootstrap Tables
        ('<table.*?>','<table class="table table-striped table-bordered">'),
        ('<thead.*?>','<thead class="thead-dark">'),
        ('(<t[r|d|h]) .*?>','\\1>'),
         # Wrap '.importantfact' in alert.info
        ('(<p class="importantfact">.*?</p>)', '<div class="alert alert-info" role="alert"> \\1 </div>'),
        ]

        extendedmpsubs = [
        # FOR MP TO ADD THEIR OWN SUBSITUTIONS
        ]

        strings_replaced = replacestrings(
            self,
            edit,
            type,
            substitutions,
            deepsubs,
            mpsubs,
            canvassubs,
            linebreaks,
            extendedmpsubs,
            config=config,
        )
        tags_removed = cleanup_structure(self, edit, type, config=config)
        summary = "CleanHTML ({mode}): {strings} substitutions, {tags} tags removed{suffix}".format(
            mode=type,
            strings=strings_replaced,
            tags=tags_removed,
            suffix="" if config.get("run_htmlprettify_after_clean", True) else ", prettify skipped",
        )
        print(summary)
        self.view.set_status("CleanHTML summary", summary)
        sublime.set_timeout(lambda: self.view.erase_status("CleanHTML summary"), 8000)

# Perform all text substitutions and string manipulations
def replacestrings(self, edit, type, substitutions, deepsubs, mpsubs, canvassubs, linebreaks, extendedmpsubs, config):
    strings_replaced = 0
    # select all and join
    self.view.run_command("select_all")
    self.view.run_command("join_lines")
    # convert to string
    sel = self.view.sel()
    string = self.view.substr(sel[0])

    # Fringe case.  If HTML contains <audio>, move this to top of page and clear floats
    if config.get("hoist_audio_to_top", True) and "<audio" in string and not string.startswith('<audio'):
        string = re.sub('(.*)(<audio.*?</audio>)(.*)','\\2<div class="clearfix container-fluid"></div>\\1\\3', string)


    # Account for additional substitutions
    if type == "mp":
        substitutions.extend(mpsubs)

    if type == "mpextended":
        substitutions.extend(extendedmpsubs)

    if type == "deep" or type == "table":
        substitutions.extend(deepsubs)

    # Loop through substitutions
    for old, new in substitutions:
        strings_replaced += len(re.findall(old, string))
        string = re.sub(old, new, string)

    if config.get("repair_nested_paragraph_wrappers", True):
        string = repair_nested_paragraph_wrappers(string)
    if config.get("normalize_external_links", True):
        string = normalize_external_links(string)

    # For Canvas
    if type == "canvas":
        # Loop through substitutions
        for old, new in canvassubs:
            strings_replaced += len(re.findall(old, string))
            string = re.sub(old, new, string)
    else:
        # Add back in whitespace
        for old, new in linebreaks:
            strings_replaced += len(re.findall(old, string))
            string = re.sub(old, new, string)

    # Output to view
    self.view.replace(edit, sel[0], string)

    return strings_replaced

def cleanup_structure(self, edit, type, config):
    self.view.run_command("select_all")
    sel = self.view.sel()
    string = self.view.substr(sel[0])
    string, tags_removed = clean_html_structure(string, type, config)
    self.view.replace(edit, sel[0], string)
    self.view.run_command("select_all")
    if config.get("run_htmlprettify_after_clean", True):
        self.view.run_command("htmlprettify")
    self.view.sel().clear()
    return tags_removed
