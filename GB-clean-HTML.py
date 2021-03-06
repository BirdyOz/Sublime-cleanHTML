import sublime, sublime_plugin, re

class CleanHtml(sublime_plugin.TextCommand):
    # Type = normal - Remove spans, font-sizes, non-breaking spaces empty tags etc.
    # Type = deep - Normal + style attributes
    # Type = table - Deep plus table tags

    def run(self, edit, type):

        # Update status image
        status_msg = "Clean HTML = " + type + " cleaning"
        self.view.set_status('cleaning',status_msg)

                                                                             # NORMAL SUBSTITUTIONS
        substitutions = [                                                    # ====================
        ('&nbsp;', ' '),                                                     # Non breaking spaces
        (' style *= *\"font-size: 1rem;\"', ''),                             # font-sizes
        (' id *= *\"yui.*?\"', ''),                                          # yui id's
        (' dir=\"ltr\"', ''),                                                # redundant LTR declarations
        (' style=\"text-align: left;\"', ''),                                # redundant text aligns
        ('(<li>)[ \#\*•-]+', '\\1'),                                         # li's that start with 1,•,#,* etc.
        ('(<[^>]*class=\"[^>]*)(Bodycopyindented|rspkr_dr_added) *', '\\1'), # specific classes
        ('(<[^>]*)(class|id|style)=\" *\"','\\1'),                           # specific empty attributes
        (' dir="ltr" style="text-align: left;"',''),                         # Get rid of ATTO's default para style on blank pages
        ('<br>\w?</p>','</p>'),                                              # br just before a closing p
        ('<\!-- ?\[(if|end).*?-->',''),                                      # MSWord style comments
        ('(<img[^>]+)\\?time=\\d{13,}','\\1'),                               # images with time stamps.  Prevents Moodle errors
        (' target="_blank"',''),                                             # Momentarily delete target="_blank"
        ('(<a[^>]*?href ?= ?"https?://.*?")','\\1 target="_blank"')          # Now add it back in for all external hrefs
        ]
                                                                             # DEEP SUBSTITUTIONS
        deepsubs = [                                                         # ==================
        (' style=\".*?\"',''),                                               # Remove all style attributes
        (' [^a][\w-]+=" *"(?=.*?>)','')                                      # Remove empty attributes that are not alt
        ]
                                                                             # TAGS TO BE REMOVED
        tags = [                                                             # ==================
        '<span',                                                             # any span (with or without attributes)
        '<section',                                                          # any section
        '<article',                                                          # any article
        '<div>',                                                             # div without attribuites
        '<li>\\W*<p',                                                        # li>p
        '<ul>\\W*<ul',                                                       # ul>ul
        '<ol>\\W*<ol',                                                       # ol>ol
        '<((p|strong|em|li|h[1-6]|b|ol|ul))>\s*(?=</\\1>)',                  # specific empty tags
        '<p>(?=\\W*<(p|ul|ol|h[1-6]|li|div|br))',                            # p>p or p>ul or p>div etc.
        '<h[1-6]><(strong|b|i|em)',                                          # headings with bolded text etc
        '/mod/glossary/showentry.php',                                       # Remove Moodle glossary links
        '<(a|img) [^>]+readspeaker\.com'                                     # Remove Readspeaker links and icons
        ]
                                                                             # ADD BACK IN WHITESPACE
        linebreaks = [                                                       # ======================
        ('(<!--|<br>|<img|<small)', '\\n\\1'),                               # breaks before certain tags
        ('(<!-- Start [^>]*-->)', '\\n\\1'),                                 # Extra line before Start of comment block
        ('(<!-- End [^>]*-->)', '\\1\\n\\n')                                 # Extra after end of comment block
        ]

        replacestrings(self, edit, type, substitutions, deepsubs, linebreaks)
        removetags(self, edit, type, tags)

# Perform all text substitutions and string manipulations
def replacestrings(self, edit, type, substitutions, deepsubs, linebreaks):
    strings_replaced = 0
    # select all and join
    self.view.run_command("select_all")
    self.view.run_command("join_lines")
    # convert to string
    sel = self.view.sel()
    string = self.view.substr(sel[0])

    # Fringe case.  If HTML contains <audio>, move this to top of page and clear floats
    if "<audio" in string and not string.startswith('<audio'):
        string = re.sub('(.*)(<audio.*?</audio>)(.*)','\\2<div class="clearfix container-fluid"></div>\\1\\3', string)


    # Loop through substitutions
    for old, new in substitutions:
        strings_replaced += len(re.findall(old, string))
        string = re.sub(old, new, string)

    # For Deep and table Clean
    if type == "deep" or type == "table":

        # Loop through substitutions
        for old, new in deepsubs:
            strings_replaced += len(re.findall(old, string))
            string = re.sub(old, new, string)

    # Add back in whitespace
    for old, new in linebreaks:
        strings_replaced += len(re.findall(old, string))
        string = re.sub(old, new, string)

    # Output to view
    self.view.replace(edit, sel[0], string)

    # Update status message
    status_msg = "Strings replaced = " + str(strings_replaced)
    self.view.set_status('str_replaced',status_msg)

# Highlight and remove unneccesary tags
def removetags(self, edit, type, tags):
    self.view.sel().clear()

    # Select all tags
    for tag in tags:
        for rgn in self.view.find_all(tag):
            # Position cursor outside (after) sel
            self.view.sel().add(rgn.end())

    # If cleaning tables as well
    if type == "table":

        for rgn in self.view.find_all('<table|<tbody|<tr|<th|<thead|<td|<caption'):
            self.view.sel().add(rgn.end())


    # Update status image
    status_msg = "Tags removed = " + str(len(self.view.sel()))
    self.view.set_status('tags_removed',status_msg)

    # Remove tags and prettify
    self.view.run_command("emmet_remove_tag")
    self.view.run_command("select_all")
    self.view.run_command("htmlprettify")
    self.view.sel().clear()