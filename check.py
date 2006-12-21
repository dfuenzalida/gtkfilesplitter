#!/usr/bin/env python
# check.py -- check for system requirements
# public domain
NAME = "gtkfilesplitter"

import sys

if __name__ == "__main__":

##########
    print "Checking Python version:",
    print ".".join(map(str, sys.version_info[:2]))
    if sys.version_info <= (2, 4):
        raise SystemExit("%s requires at least Python 2.4."
                         "(http://www.python.org)" % NAME)
##########

    print "Checking for PyGTK >= 2.6:",
    try:
        import pygtk
        pygtk.require('2.0')
        import gtk
        if gtk.pygtk_version < (2, 6) or gtk.gtk_version < (2, 6):
            raise ImportError
    except ImportError:
        raise SystemExit("not found\n%s requires PyGTK 2.6. "
                         "(http://www.pygtk.org)" % NAME)
    else: print "found"

##########

