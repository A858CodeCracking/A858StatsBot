#!/usr/bin/env python

# Copyright: this file has been released into the public domain.

"""A858 statistics.

This module provides the class LastPostStats which parses the data from
the A858 auto-analysis site (a858.soulsphere.org).
"""

import re
import sys
import datetime
import requests
from bs4 import BeautifulSoup as bs

# Compatible with v2 and v3
if sys.version_info.major < 3:
    range = xrange  # noqa

REGEXES = {"length": r"(Length: (\d+) bytes \(= \d+ \+ \d+ \* \d+\))",
           "distrib": r"(Statistical distribution: (.+ \(.+ stddevs\)))",
           "posted": (r"(Posted to Reddit: "
                      "(\w{3} \w{3} \s?\d{1,2} \d{2}:\d{2}:\d{2} \d{4} UTC))"),
           "delay": r"(Post delay: (\d+) seconds)",
           "timezone": r"Identified time zone:",
           "mimetype": r"(File type \(MIME\): ([^<]*))"}


# Regex helper function - use group=2 for raw data
def re_search(regex, string, group=1):
    return re.search(regex, string).group(group)


class LastPostStats(object):

    """A858 statistics."""

    def __init__(self, from_url="http://a858.soulsphere.org/"):
        self._url = from_url
        self.update()

    def update(self):
        """Retrieve fresh data."""
        page_html = requests.get(self._url).text
        page_soup = bs(page_html)
        self._soup = page_soup.find(id=re.compile(r"^post-\w{6}$"))
        self._html = self._soup.decode(formatter=None)
        self._parse()

    def _parse(self):
        """Parse the original HTML."""
        self.length = re_search(REGEXES["length"], self._html)
        self.distrib = re_search(REGEXES["distrib"], self._html)
        self.title = self._soup.h3.string
        self.time = "Time in post title: {}".format(self._strftime(self.title))
        self.posted = re_search(REGEXES["posted"], self._html)
        self.delay = re_search(REGEXES["delay"], self._html)
        self.mime = re_search(REGEXES["mimetype"], self._html)
        self.id36 = self._soup.a["name"]
        self._tz = self._soup.find(text=re.compile(REGEXES["timezone"])).next
        self.tz_link = self._tz["href"]
        self.tz_str = "{text} {tz}".format(text=REGEXES["timezone"],
                                           tz=self._tz.string)
        self.tz_int = int(self._tz.string[3:])

    def _strftime(self, timestamp):
        time = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M")
        return time.strftime("%c")

    def __str__(self):
        msg = ("{length}\n\n"
               "{distrib}\n\n"
               "{time}\n\n"
               "{posted}\n\n"
               "[{tz_str}]({tz_link})\n\n"
               "{delay}\n\n"
               "{mimetype}\n"
               ).format(length=self.length,
                        distrib=self.distrib,
                        time=self.time,
                        posted=self.posted,
                        tz_str=self.tz_str,
                        tz_link=self.tz_link,
                        delay=self.delay,
                        mimetype=self.mime)
        return msg


def main():
    post = LastPostStats()
    print(str(post))

if __name__ == "__main__":
    main()
