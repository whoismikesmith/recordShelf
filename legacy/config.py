#!/usr/bin/env python

"""config.py: config for app.py"""

import os

__author__		= "Mike Smith"
__copyright__	= "Copyright 2017, Mike Smith"
__license__		= "MIT"
__maintainer__	= "Mike Smith"

discogsUsername = os.environ["DISCOGS_USERNAME"]
#default page number
pageNumber = "1"
#valid sorts : label artist title catno format rating added year
sort = "artist"
defaultFormats = ["LP","12\""]
