import sublime, sublime_plugin, re

class CleanMd(sublime_plugin.TextCommand):

    def run(self, edit, type):

        # Update status image
        status_msg = "Clean MD = " + type + " cleaning"
        self.view.set_status('cleaning',status_msg)

        substitutions = [
        ('[·•] +', '* '),                    # Replace bullets with *
        ('^\\\(\d\.) +', '\\1 '),            # Replace \1. etc with 1.
        ('# +\n', ''),                       # Empty headings
        ('((# |\*|\d\.)) {2,}', '\\1 '),     # Blank spaces before headings, bulets, numbers
        ('# \*\*(.*?)\*\*', ' \\1'),         # Bolded headings
        ('(^\* .*)\n{2,}(?=\*)', '\\1\n'),   # Collapse lines b/n bullets
        ('(^\d\. .*)\n{2,}(?=\d)', '\\1\n'), # Collapse lines b/n numbered lists
        ('\n{3,}', '\n\n')                   # Multiple empty lines
        ]

        replacestrings(self, edit, type, substitutions)

# Perform all text substitutions and string manipulations
def replacestrings(self, edit, type, substitutions):
    strings_replaced = 0
    # select all
    self.view.run_command("trim_trailing_whitespace")
    self.view.run_command("select_all")
    # convert to string
    sel = self.view.sel()
    string = self.view.substr(sel[0])

    # Loop through substitutions
    for old, new in substitutions:
        strings_replaced += len(re.findall(old, string, flags=re.MULTILINE))
        string = re.sub(old, new, string, flags=re.MULTILINE)

    # Add Bootstrap support
    bootstrap = '<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">\n<script src="https://code.jquery.com/jquery-3.4.1.slim.min.js" integrity="sha384-J6qa4849blE2+poT4WnyKhv5vZF5SrPo0iEjwBvKU7imGFAV0wwj1yYfoRSJoZ+n" crossorigin="anonymous"></script>\n<script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js" integrity="sha384-Q6E9RHvbIyZFJoft+2mJbHaEWldlvI9IOYy5n3zV9zzTtmI3UksdQRVvoxMfooAo" crossorigin="anonymous"></script>\n<script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js" integrity="sha384-wfSDF2E50Y2D1uUdj0O3uMBJnjuUD4Ih7YwaYd1iqfktj0Uod8GCExl3Og8ifwB6" crossorigin="anonymous"></script>\n<link href="https://netdna.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet">\n\n'

    if "bootstrapcdn" not in string:
        string = bootstrap + string


    # Output to view
    self.view.replace(edit, sel[0], string)

    # Update status
    status_msg = "Strings replaced = " + str(strings_replaced)
    self.view.set_status('str_replaced',status_msg)

    # Launch in browser
    self.view.run_command("omni_markup_preview")

