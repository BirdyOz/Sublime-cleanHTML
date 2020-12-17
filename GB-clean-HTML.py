import sublime, sublime_plugin, re

class CleanHtml(sublime_plugin.TextCommand):
    # Type = nomal - Remove spans, font-sizes, non-breaking spaces empty tags etc.
    # Type = deep - Normal + style attributes
    # Type = table - Deep plus table tags

    def run(self, edit, type):

        # Update status image
        status_msg = "Clean HTML = " + type + " cleaning"
        self.view.set_status('cleaning',status_msg)
                                                              # NORMAL SUBSTITUTIONS
        substitutions = [                                     # -------------------
        ('&nbsp;', ' '),                                      # Non breaking spaces
        (' style *= *\"font-size: 1rem;\"', ''),              # font-sizes
        (' id *= *\"yui.*?\"', ''),                           # yui id's
        ('(<li>)[1-9\. \#\*•]+', '\\1'),                      # li's that start with 1,•,#,* etc.
        ('(<[^>]*class=\"[^>]*)(Bodycopyindented) *', '\\1'), # specific classes
        ('(<[^>]*)(class|id|style)=\" *\"','\\1'),            # specific empty attributes
        ]

                                                              # DEEP SUBSTITUTIONS
        deepsubs = [                                          # ------------------
        (' style=\".*?\"',''),                                # Remove style attributes
        (' [^a][\w-]+=" *"(?=.*?>)','')                       # Remove empty attributes that are not alt
        ]

                                                              # TAGS TO BE REMOVED
        tags = [                                              # ------------------
        '<span',                                              # any span (with or without attributes)
        '<section',                                           # any section
        '<article',                                           # any article
        '<div>',                                              # div without attribuites
        '<li>\\W*<p',                                         # li>p
        '<ul>\\W*<ul',                                        # ul>ul
        '<ol>\\W*<ol',                                        # ol>ol
        '<((p|strong|em|li|h[1-6]|b|ol|ul))>\s*(?=</\\1>)',   # specific empty tags
        '<p>(?=\\W*<(p|ul|ol|h[1-6]|li|div|br))',             # p>p or p>ul or p>div etc.
        '<br(?=>\\W*</p)'                                     # br inside closing </p>
        ]

        replacestrings(self, edit, type, substitutions, deepsubs)
        removetags(self, edit, type, tags)

# Perform all text substitutions and string manipulations
def replacestrings(self, edit, type, substitutions, deepsubs):
    strings_replaced = 0
    # select all and join
    self.view.run_command("select_all")
    self.view.run_command("join_lines")
    # convert to string
    sel = self.view.sel()
    string = self.view.substr(sel[0])

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

    # Add back in newlines for specific tags
    string = re.sub('(<!--|<br>|<img|<small)', '\\n\\1', string)

    # Output to view
    self.view.replace(edit, sel[0], string)

    # Update status
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
