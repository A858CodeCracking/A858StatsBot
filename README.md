A858StatsBot
============

A Reddit bot which publishes the statistics from the [a858
auto-analysis][analysis] site as comments to A858's posts.

What the duck is A858?
----------------------

*A858* is the Star-Wars-like short name given to the Reddit user
[A858DE45F56D9BC9][ua858] by the Reddit community.

A858 is maybe the biggest mistery on Reddit.  Several theories have been raised
on who or what is A858.  You can find these theories in the wiki of a dedicated
subreddit where people are trying to crack A858's code: [Solving_A858][solving].

How it works
------------

This bot parses the homepage of the site <http://a858.soulsphere.org/> searching
for the newest post.  If the post has not been parsed yet, the bot retrieves
the raw data from it (including the ID of original post on Reddit) and post
them as a comment to the related Reddit post from A858 itself.

The purpose is to present these statistics directly when opening a post by
A858.

Future
------

If the bot doesn't get banned from the A858 subreddit, the plan is to extend
its features to provide even more information on A858's posts.

If it *does* get banned
-----------------------

The code will still remain for educational purposes.

Get the code working
--------------------

This script uses the following Python modules:

 - BeautifulSoup (HTML parsing)
 - requests (HTTP requests)
 - PRAW (Reddit API)

Install them (as root) with the following command:

    pip install beautifulsoup4 requests praw

If you don't have `pip` installed, follow [these][pip] simple instructions.
You can also try to install the `python-pip` package for your Linux distro.

Install the bot
---------------

The first step is to create a configuration file `.a858rc` (see next section
for details).

Locate the script `a858statsbot.py` (the main program) in the bot's home
folder.  This script must be able to import `a858stats.py` and `a858utils.py`,
so make sure they are in a folder included in the PYTHONPATH or the same folder
as the main script.

The bot is running on a Raspberry Pi with Raspbian, so I also wrote a Debian
init script to run it as a daemon.  First of all create the user
`a858statsbot`.  Copy the script `a858statsbot` in `/etc/init.d` and make it
executable with (as root):

    chmod +x /etc/init.d/a858statsbot

Then, to run it (as root):

    /etc/init.d/a858statsbot start

and, in order to make it run on startup, (as root):

    chmod update-rc.d a858statsbot defaults

### Note about the filenames

Yeah, I know, I could've thought of better names for the scripts: this whole
`a858stats*` thing may seem a little confusing.  But, well, what's done is
done, my code my rules :P

Config file
-----------

This file (`.a858rc`) must be placed in the bot user's home folder.

The file structure is simple:

    python_var      value of the python var
    # lines beginning with '#' or empty lines are ignored
    whitespaces     after the variable and before the value are stripped

### Values

    delay           seconds to wait before checking for new data
    username        reddit bot username
    password        reddit bot password
    useragent       reddit bot useragent
    footer          comment footer
    author          the bot author
    smtp_server     smtp server address
    smtp_port       smtp port
    smtp_tls        True or False
    email_to        email address to which pms to the bot will be forwarded
    email_from      from field for the forwarded email
    email_username  empty or not specified if don't need authentication
    email_password  email account password

Contributions
-------------

Should you have any suggestions, feel free to contact me, open an issue or send
a pull request.

The code in the pull requests must abide by [PEP8][pep8] and by
[PEP257][pep257]: `flake8` must pass without errors/warnings.

[analysis]: http://a858.soulsphere.org/
[ua858]: http://www.reddit.com/u/A858DE45F56D9BC9/
[solving]: http://www.reddit.com/r/Solving_A858/
[pip]: http://www.pip-installer.org/en/latest/installing.html
[pep8]: http://legacy.python.org/dev/peps/pep-0008/
[pep257]: http://legacy.python.org/dev/peps/pep-0257/
