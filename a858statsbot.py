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
from requests.exceptions import HTTPError

RC_FILE = "~/.a858rc"
CACHE_FILE = "~/.a858cache"
LOG_CONF_FILE = "~/a858sblogger.conf"

# Logger initialization
logging.config.fileConfig(a858utils.expand(LOG_CONF_FILE))
logger = logging.getLogger(__name__)


def handle_http_error(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except HTTPError as err:
            logger.error("HTTP error: {}".format(err))
    return wrapper


class Bot(object):

    """Main bot class."""

    cache_file = CACHE_FILE

    def __init__(self, configs):
        self._load_configs(configs)
        # Initialize PRAW and connect to Reddit
        logger.debug("Connecting to Reddit")
        self._init_praw()
        # Initialize the cache
        logger.debug("Initializing cache")
        self.cache = a858utils.Cache(a858utils.expand(self.cache_file))
        # Set to False to break the main loop
        self.running = True

    def _load_configs(self, configs):
        self.delay = configs["delay"]
        self.signature = configs["footer"]
        # Reddit config
        self.useragent = configs["useragent"]
        self.username = configs["username"]
        self.password = configs["password"]
        # PMs
        if ("ignore_from" in configs.keys()):
            self.ignore_from = configs["ignore_from"].lower().split()
        else:
            self.ignore_from = []
        # Email config
        if ("email_username" in configs.keys() and
                configs["email_username"]):
            self.email_username = configs["email_username"]
            self.email_password = configs["email_password"]
        else:
            self.email_username = ""
            self.email_password = ""
        self.email_from = configs["email_from"]
        self.email_to = configs["email_to"]
        if ("smtp_tls" in configs.keys() and configs["smtp_tls"]):
            self.smtp_tls = configs["smtp_tls"]
        else:
            self.smtp_tls = False
        self.smtp_server = configs["smtp_server"]
        self.smtp_port = configs["smtp_port"]

    @handle_http_error
    def _init_praw(self):
        self.r = praw.Reddit(self.useragent)
        self.r.login(self.username, self.password)

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
        m = a858utils.Mailer(self.smtp_server,
                             self.smtp_port,
                             bool(self.smtp_tls))
        try:
            m.connect()
            # email_username key exists and its value is not None
            if self.email_username:
                m.auth(self.email_username, self.email_password)
            m.send_mail(self.email_from,
                        self.email_to,
                        " PM from {}: {}".format(author, subject),
                        body)
            logger.debug("PM from {} forwarded".format(author))
        except a858utils.MailError as err:
            logger.error(err)
        finally:
            m.disconnect()

    def stop(self):
        """Stop the main loop."""
        self.running = False

    @property
    @handle_http_error
    def pms(self):
        return self.r.get_unread()

    @handle_http_error
    def check_pms(self):
        """Check for unread PMs on the bot's account."""
        for m in self.pms:
            author = m.author.name
            # Usernames are case sensitive
            if author.lower() in self.ignore_from:
                logger.debug("Ignoring PM from {}".format(author))
                m.mark_as_read()
                continue
            subject = m.subject
            body = m.body
            logger.debug("Forwarding PM from {}".format(author))
            self._forward_pm(author, subject, body)
            m.mark_as_read()
            logger.debug("PM from {} marked as read".format(author))

    @handle_http_error
    def get_submissio(self, submission_id):
        return self.r.get_submission(submission_id=submission_id)

    @handle_http_error
    def post_comment(self, r_submission, text):
        r_submission.add_comment(text)

    def run(self):
        """Main loop."""
        while self.running:
            self.check_pms()

            last_stat = a858stats.LastPostStats()
            logger.debug("Parsed stats for post id {}".format(last_stat.id36))

            if last_stat.id36 in self.cache:
                logger.debug("Post in cache, sleeping...")
                sleep(int(self.delay))
                continue

            last_post = self.get_submission(last_stat.id36)
            logger.debug("Reddit post with id {} found".format(last_stat.id36))

            comment = self._build_comment(str(last_stat), self.signature)

            logger.debug("Posting comment")
            self.post_comment(last_post, comment)

            logger.debug("Caching post ID")
            self.cache.add(last_stat.id36)
            self.cache.save()

if __name__ == "__main__":
    import sys
    logger.debug("Loading configuration file")
    try:
        configs = a858utils.parse_rc_file(RC_FILE)
    except a858utils.ConfigFileError as err:
        logger.critical(err)
        sys.exit(1)
    try:
        Bot(configs).run()
    except Exception as err:
        logger.exception(err)
        sys.exit(1)
