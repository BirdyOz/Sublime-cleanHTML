import sublime, sublime_plugin, re, sys

class CleanHtml(sublime_plugin.TextCommand):
    # Type = normal - Remove spans, font-sizes, non-breaking spaces empty tags etc.
    # Type = deep - Normal + style attributes
    # Type = table - Deep plus table tags

    def run(self, edit, type):

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
        ('(<li>)[ \#\*•·-]+', '\\1'),                                        # li's that start with •,#,* etc.
        ('(<li>)[1-9]+\. *', '\\1'),                                         # li's that start with a number
        ('(<[^>]*class=\"[^>]*)(Bodycopyindented|rspkr_dr_added) *', '\\1'), # specific classes
        ('(<[^>]*)(class|id|style)=\" *\"','\\1'),                           # specific empty attributes
        (' dir="ltr" style="text-align: left;"',''),                         # Get rid of ATTO's default para style on blank pages
        ('<p><br></p>','<br>'),                                              # p's that only contain br
        ('<br>\w?</p>','</p>'),                                              # br just before a closing p
        ('<\!-- ?\[(if|end).*?-->',''),                                      # MSWord style comments
        ('(<img[^>]+)\\?time=\\d{13,}','\\1'),                               # images with time stamps.  Prevents Moodle errors
        # ('(<img[^>]+)width="\d+\%?" height="\d+\%?" ','\\1'),              # remove image dimensions
        ('http://127.0.0.1.*?\#','#'),                                       # remove localhost prefix
        (' atto_image_button_text-bottom',' w-100'),                         # remove img classes added by the ATTO editor
        ('(?<=<td)(?<!>) width="\d+\%?"',''),                                # remove <td> widths
        (' valign="top"',''),                                                # remove <td> valign="top"
        (' target="_blank"',''),                                             # Momentarily delete target="_blank"
        ('(<a[^>]*?href ?= ?"https?://.*?")','\\1 target="_blank"'),         # Now add it back in for all external hrefs
        ('<a class="source-btn" data-toggle="collapse" href="#show',         # Specific cleanup of attribution helpers
        '<a class="source-btn text-muted" data-toggle="collapse" href="#show'),
        ('▼ Show attribution', '▽ Show attribution')
        ]
                                                                             # TAGS TO BE REMOVED
        tags = [                                                             # ==================
        '<span style="font-size: 1rem;.*?\""',                               # spans with 1rem sizing (Moodle ATTO artefact)
        '<span lang="EN-US"',                                                # spans with lang
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
        '<a name="',                                                         # Remove MsWord internal anchors
        '<(a|img) [^>]+readspeaker\.com'                                     # Remove Readspeaker links and icons
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
        (' style=\".*?\"',''),                                               # Remove all style attributes
        (' [^a][\w-]+=" *"(?=.*?>)','')                                      # Remove empty attributes that are not alt
        ]
                                                                             # CANVASLMS SUBSTITUTIONS
        canvassubs = [                                                       # ==================
        ('data-mce-.*?".*?" ?', ''),                                         # Canvas MCE editor
        (' target="_blank"',''),                                             # Delete all target="_blank"
        ('<!--.*?-->',''),                                                   # Delete all comments
        ('<br>',''),                                                         # Delete <br>
        ('<div style="display: block;" class="ghost-text-message">Connected! You can switch to your editor</div>','')
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
        ('<p class="weblink">(Weblink:|)*(.*?)</p> <p><a href="https://(youtu\.be/|www\.youtube\.com/watch\?v=)(.*?)".*?</p>', '<div class="clearfix container-fluid"></div> <div class="card mt-1 mb-1"> <div class="card-body"> <h4 class="text-danger yt-title"><i class="fa fa-play-circle-o"></i> \\2</h4> <div class="embed-responsive embed-responsive-16by9"> <iframe id="yt-placeholder" class="embed-responsive-item vjs-tech" frameborder="0" allowfullscreen="1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" title="\\2" width="100%" height="100%" src="https://www.youtube.com/embed/\\4?modestbranding=1&amp;rel=0&amp;enablejsapi=1&amp;origin=https%3A%2F%2Fbirdyoz.github.io&amp;widgetid=1" data-gtm-yt-inspected-4="true"></iframe> </div> </div> </div>'),
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

        replacestrings(self, edit, type, substitutions, deepsubs, mpsubs, canvassubs, linebreaks, extendedmpsubs)
        removetags(self, edit, type, tags)

# Perform all text substitutions and string manipulations
def replacestrings(self, edit, type, substitutions, deepsubs, mpsubs, canvassubs, linebreaks, extendedmpsubs):
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

    # Update status message
    status_msg = "Strings replaced = " + str(strings_replaced)

    self.view.set_status("Strings replaced", status_msg)
    sublime.set_timeout(lambda: self.view.erase_status("Strings replaced"), 8000)

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

    self.view.set_status("Tags removed", status_msg)
    sublime.set_timeout(lambda: self.view.erase_status("Tags removed"), 8000)

    # Remove tags and prettify
    self.view.run_command("emmet_remove_tag")
    self.view.run_command("select_all")
    self.view.run_command("htmlprettify")
    self.view.sel().clear()