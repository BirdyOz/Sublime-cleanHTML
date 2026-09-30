# Retired Melbourne Polytechnic transformations

Archived on 2026-09-30 from baseline commit `d44baa9`, pushed before the settings refactor.
This file is documentation only: it is not loaded or executed by Sublime.
The `mp` and `mpextended` modes and palette entries have been retired.

The original rules included paragraph-to-list conversion, image/attribution figures,
learning-activity cards, YouTube cards, weblink conversion, Bootstrap table styles,
and important-fact alerts. Their original order mattered. They assumed particular
attribute orders, whitespace, client URLs, Bootstrap classes, and image markup.
Do not enable these wholesale in the new cleaner. Recover only the transformation
needed, scope it to the relevant elements, and add input/preservation fixtures.

The old list grouping could leave an LI outside a UL and add nested ULs on each run.
Table rules discarded attributes, YouTube cards reused one iframe ID, and the fixed
origin/query values were specific to a historic workflow. MP Extended's list was
empty and was not an extension of the ordinary MP list.

## Exact historical substitution lists

```python
mpsubs = [                                                           # ==================
('<p class="(bulletlist|standardbulletpoint)".*?>(.*?)</p>','<li>\\2</li>'), # Convert p bullets into li
('(( <li>.*?</li>)+)','<ul>\\1</ul>'),                               # Wrap converted list groups in ul
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

```

The September TinyMCE baseline also unwrapped non-protected `span` elements in MP
mode after structural cleanup. Earlier versions removed both span opening and
closing tags through regex. Neither operation is active in the refactored cleaner.

## Other retired migration behavior

The Canvas mode formerly replaced the following numbers throughout the entire
HTML document. This map is retained here for reference and deliberately has no
active replacement rule: `9864→9948`, `9865→9949`, `9866→9947`, `9867→9946`,
`9868→9945`, `9869→9944`, `9870→9943`, `9871→9942`, `9872→9941`, `9873→9940`.
If reused, scope replacement to the actual source URL attribute and environment.
Canvas comment/target cleanup remains configurable in the new settings.

Full original source is available in Git at `d44baa9:GB-clean-HTML.py`.
