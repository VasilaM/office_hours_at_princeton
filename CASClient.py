#!/usr/bin/env python

# -----------------------------------------------------------------------
# CASClient.py
# Authors: Alex Halderman, Scott Karlin, Brian Kernighan, Bob Dondero
# -----------------------------------------------------------------------

import urllib.request
import urllib.parse
import flask
from sys import stderr
import re

# -----------------------------------------------------------------------


class CASClient:

    # -------------------------------------------------------------------

    # Initialize a new CASClient object so it uses the given CAS
    # server, or fed.princeton.edu if no server is given.

    def __init__(self, url="https://fed.princeton.edu/cas/"):
        self.cas_url = url

    # -------------------------------------------------------------------

    # Return True if user is logged in

    def is_logged_in(self):
        return "username" in flask.session

    # -------------------------------------------------------------------

    # Return the URL of the current request after stripping out the
    # "ticket" parameter added by the CAS server.

    def strip_ticket(self, url):
        if url is None:
            return "something is badly wrong"
        url = re.sub(r'ticket=[^&]*&?', '', url)
        url = re.sub(r'\?&?$|&$', '', url)
        return url
    # -------------------------------------------------------------------

    # Validate a login ticket by contacting the CAS server. If
    # valid, return the user's username; otherwise, return None.

    def validate(self, ticket):
        val_url = (self.cas_url + "validate" + '?service='
            + urllib.parse.quote(self.strip_ticket(flask.request.url))
            + '&ticket=' + urllib.parse.quote(ticket))
        lines = []

        with urllib.request.urlopen(val_url) as flo:
            lines = flo.readlines()   # Should return 2 lines.
        if len(lines) != 2:
            return None
        first_line = lines[0].decode('utf-8')
        second_line = lines[1].decode('utf-8')
        if not first_line.startswith('yes'):
            return None
        return second_line

    # -------------------------------------------------------------------

    # Authenticate the remote user, and return the user's username.
    # Do not return unless the user is successfully authenticated.

    def authenticate(self):

        # If the username is in the session, then the user was
        # authenticated previously.  So return the username.
        if 'username' in flask.session:
            return flask.session.get('username')

        # If the request does not contain a login ticket, then redirect
        # the browser to the login page to get one.
        ticket = flask.request.args.get('ticket')
        if ticket is None:
            login_url = (self.cas_url + 'login?service=' +
                urllib.parse.quote(flask.request.url))
            print(login_url)
            flask.abort(flask.redirect(login_url))
        # If the login ticket is invalid, then redirect the browser
        # to the login page to get a new one.
        username = self.validate(ticket)
        if username is None:
            login_url = (self.cas_url + 'login?service='
                + urllib.parse.quote(self.strip_ticket(flask.request.url)))
            login_url = login_url.replace("127.0.0.1", "localhost")

            flask.abort(flask.redirect(login_url))

        # The user is authenticated, so store the username in
        # the session.
        username = username.strip()
        flask.session['username'] = username
        return username

    # -------------------------------------------------------------------

    # Logout the user.

    def logout(self):
        # Delete the user's username from the session.
        flask.session.pop("username")
        # Redirect the browser to the application's home page.
        flask.abort(flask.redirect("/landing-page"))


# -----------------------------------------------------------------------


def main():
    print("CASClient does not run standalone")


if __name__ == "__main__":
    main()