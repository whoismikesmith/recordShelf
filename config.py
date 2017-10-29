# app.py
import os

discogsUsername = os.environ["DISCOGS_USERNAME"]
#default page number
pageNumber = "1"
#valid sorts : label artist title catno format rating added year
sort = "artist"
defaultFormats = ["LP","12\""]
