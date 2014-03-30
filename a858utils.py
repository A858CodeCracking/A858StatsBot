"""A858 utilities.

This module provides the following utility classes:
    * Cache
    * Mailer
and the following helper functions:
    * expand
    * get_fortune
"""

import pickle
import smtplib
import os.path
import requests
from collections import deque
from email.mime.text import MIMEText


# Helper functions

def expand(path):
    """Return the expanded path."""
    return os.path.expandvars(os.path.expanduser(path))


def get_quote():
    """Get a quote from ihearquotes.com."""
    url = "http://www.iheartquotes.com/api/v1/random"
    params = {"max_lines": "1", "format": "json"}
    return requests.get(url, params=params).json()["quote"]


def sup(text):
    """Prepend the caret symbol (^) to every word in text

    Return a string."""
    msg = ""
    for line in text.splitlines():
        for word in line.split():
            msg += "^" + word + " "
        msg += "\n"
    return msg.rstrip()


# Classes

class ConnectionError(Exception):
    # Handle error related to smtplib.SMTP()
    pass


class TLSError(Exception):
    # Handle error related to SMTP.starttls()
    pass


class AuthenticationError(Exception):
    # Handle error related to SMTP.login()
    pass


class SendEmailError(Exception):
    # Handle error related to SMTP.sendmail() or SMTP.send_message()
    pass


class Cache(object):

    """Permanent cache handler."""

    def __init__(self, filename, maxlen=50):
        self.filename = filename
        if os.path.exists(expand(filename)):
            self.load()
        else:
            self.cache = deque(maxlen=maxlen)

    def add(self, item):
        """Add item to cache."""
        self.cache.append(item)

    def load(self):
        """Load the cache from the cache file."""
        with open(self.filename, "rb") as cf:
            self.cache = pickle.load(cf)

    def save(self):
        """Save the cache to a file."""
        with open(self.filename, "wb") as cf:
            pickle.dump(self.cache, cf, -1)

    def __iter__(self):
        return iter(self.cache)


class Mailer(object):

    """A simple smtplib interface."""

    def __init__(self, host, port=0, tls=False):
        self.host = host
        self.port = port
        self.tls = tls

    def connect(self):
        try:
            self.server = smtplib.SMTP(self.host)
        except (smtplib.socket.error,
                smtplib.SMTPConnectError) as err:
            raise ConnectionError(err)
        if self.tls:
            try:
                self.server.starttls()
            except (smtplib.SMTPHeloError,
                    smtplib.SMTPException) as err:
                raise TLSError(err)

    def auth(self, username, password):
        try:
            self.server.login(username, password)
        except (smtplib.SMTPAuthenticationError,
                smtplib.SMTPHeloError,
                smtplib.SMTPException) as err:
            raise AuthenticationError(err)

    def send_mail(self, from_, to, subject, message):
        msg = MIMEText(message, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_
        msg["To"] = to
        try:
            # if sys.version_info >= (3, 2):
            #     self.server.send_message(msg)
            self.server.sendmail(from_, to, msg.as_string())
        except (smtplib.SMTPRecipientsRefused,
                smtplib.SMTPHeloError,
                smtplib.SMTPSenderRefused,
                smtplib.SMTPDataError) as err:
            raise SendEmailError(err)

    def disconnect(self):
        self.server.quit()

    close = disconnect
