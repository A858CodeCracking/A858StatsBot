#!/usr/bin/env python

# Copyright: this file has been released into the public domain.

# TODO:
# - multithreading
# - docs
# - logging
# - improve PMs forwarding

import praw
import logging
import logging.config
import a858stats
import a858utils
from time import sleep

RC_FILE = "~/.a858rc"
CACHE_FILE = "~/.a858cache"
LOG_CONF_FILE = "~/a858sblogger.conf"

# Logger initialization
logging.config.fileConfig(a858utils.expand(LOG_CONF_FILE))
logger = logging.getLogger(__name__)


class Bot(object):

    """Main bot class."""

    rc_file = RC_FILE
    cache_file = CACHE_FILE

    def __init__(self):
        # Load the configuration file
        self.configs = self.parse_rc_file(self.rc_file)
        logger.debug("Configuration file loaded")
        # Initialize PRAW and connect to Reddit
        self.r = praw.Reddit(self.configs["useragent"])
        self.r.login(self.configs["username"], self.configs["password"])
        logger.debug("Connected to Reddit")
        # Initialize the cache
        self.cache = a858utils.Cache(a858utils.expand(self.cache_file))
        logger.debug("Cache initialized")
        # Set to False to break the main loop
        self.running = True

    @staticmethod
    def parse_rc_file(rc_file):
        """Parse a config file and return a dictionary."""
        configs = []
        with open(a858utils.expand(rc_file), "r") as rc:
            l = rc.readlines()
        for i in l:
            if i == "\n" or i.lstrip()[0] == "#":
                continue
            c = i.rstrip().split(None, 1)
            if len(c) == 1:
                c.append(None)
            configs.append(c)
        return dict(configs)

    def _build_comment(self, post_data, footer_info):
        """Return a string."""
        # Get a random quote from the Internet
        quote = a858utils.get_quote()
        footer = ("{info}\n\n"
                  "^QOTPost: *{qotp}*").format(info=a858utils.sup(footer_info),
                                               qotp=a858utils.sup(quote))
        msg = ("{data}\n"
               "---\n"
               "{footer}").format(data=post_data,
                                  footer=footer)
        return msg

    def _forward_pm(self, author, subject, body):
        """Send an email to the bot author with the received PM."""
        m = a858utils.Mailer(self.configs["smtp_server"],
                             self.configs["smtp_port"],
                             bool(self.configs["smtp_tls"]))
        m.connect()
        try:
            # email_username config exists and is not None
            if ("email_username" in self.configs.keys() and
                    self.configs["email_username"]):
                m.auth(self.configs["email_username"],
                       self.configs["email_password"])
            m.send_mail(self.configs["email_from"],
                        self.configs["email_to"],
                        " PM from {}: {}".format(author, subject),
                        body)
            logger.debug("PM from {} forwarded".format(author))
        except Exception as err:
            logger.error(err)
        finally:
            m.disconnect()

    def stop(self):
        """Stop the main loop."""
        self.running = False

    def check_pms(self):
        """Check for unread PMs on the bot's account."""
        pms = self.r.get_unread()
        for m in pms:
            author = m.author.name
            # Usernames are case sensitive
            if ("ignore_from" in self.configs.keys() and
                    author.lower() in
                    self.configs["ignore_from"].lower().split()):
                logger.debug("Ignoring PM from {}".format(author))
                m.mark_as_read()
                continue
            subject = m.subject
            body = m.body
            logger.debug("Forwarding PM from {}".format(author))
            self._forward_pm(author, subject, body)
            m.mark_as_read()
            logger.debug("PM from {} marked as read".format(author))

    def run(self):
        """Main loop."""
        while self.running:
            self.check_pms()

            last_stat = a858stats.LastPostStats()
            logger.debug("Parsed stats for post id {}".format(last_stat.id36))

            if last_stat.id36 in self.cache:
                logger.debug("Post in cache, sleeping...")
                sleep(int(self.configs["delay"]))
                continue

            last_post = self.r.get_submission(submission_id=last_stat.id36)
            logger.debug("Reddit post with id {} found".format(last_stat.id36))

            comment = self._build_comment(str(last_stat),
                                          self.configs["footer"])

            last_post.add_comment(comment)
            logger.debug("Comment sent")

            self.cache.add(last_stat.id36)
            self.cache.save()
            logger.debug("Post id cached")

if __name__ == "__main__":
    Bot().run()
