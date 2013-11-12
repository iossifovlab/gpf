#!/usr/local/bin/python
"""Replacement for htpasswd"""
# Original author: Eli Carter

'''
Created on Aug 6, 2012

@author: lubo
'''


import os
import sys
import random
import string
from optparse import OptionParser

# We need a crypt module, but Windows doesn't have one by default.  Try to find
# one, and tell the user if we can't.
try:
    import crypt
except ImportError:
    try:
        import fcrypt as crypt
    except ImportError:
        sys.stderr.write("Cannot find a crypt module.  "
                         "Possibly http://carey.geek.nz/code/python-fcrypt/\n")
        sys.exit(1)



#password_len = 12
#
#def makepasswd(password_len=12):
#    password = []
#    
#    for group in (string.ascii_letters, string.punctuation, string.digits):
#        password += random.sample(group, 3)
#    
#    password += random.sample(
#                     string.ascii_letters + string.punctuation + string.digits,
#                     password_len - len(password))
#    
#    random.shuffle(password)
#    password = ''.join(password)
#
#    return password

def makepasswd1(password_len=8):
    password = []
    
    for group in (string.ascii_letters, string.digits):
        password += random.sample(group, 3)
    
    if len(password) < password_len:
        password += random.sample(
                         string.ascii_letters + string.digits,
                         password_len - len(password))
    
    random.shuffle(password)
    password = ''.join(password)

    return password



def salt():
    """Returns a string of 2 randome letters"""
    letters = 'abcdefghijklmnopqrstuvwxyz' \
              'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
              '0123456789/.'
    return random.choice(letters) + random.choice(letters)





class HtpasswdFile:
    """A class for manipulating htpasswd files."""

    def __init__(self, filename, create=False):
        self.entries = []
        self.filename = filename
        if not create:
            if os.path.exists(self.filename):
                self.load()
            else:
                raise Exception("%s does not exist" % self.filename)

    def load(self):
        """Read the htpasswd file into memory."""
        lines = open(self.filename, 'r').readlines()
        self.entries = []
        for line in lines:
            username, pwhash = line.split(':')
            entry = [username, pwhash.rstrip()]
            self.entries.append(entry)

    def save(self):
        """Write the htpasswd file to disk"""
        open(self.filename, 'w').writelines(["%s:%s\n" % (entry[0], entry[1])
                                             for entry in self.entries])

    def update(self, username, password):
        """Replace the entry for the given user, or add it if new."""
        pwhash = crypt.crypt(password, salt())
        matching_entries = [entry for entry in self.entries
                            if entry[0] == username]
        if matching_entries:
            matching_entries[0][1] = pwhash
        else:
            self.entries.append([username, pwhash])

    def delete(self, username):
        """Remove the entry for the given user."""
        self.entries = [entry for entry in self.entries
                        if entry[0] != username]


class UsersFile:
    """A class for manipulating users files."""

    def __init__(self, filename, create=False):
        self.entries = []
        self.filename = filename
        if not create:
            if os.path.exists(self.filename):
                self.load()
            else:
                raise Exception("%s does not exist" % self.filename)

    def load(self):
        """Read the users file into memory."""
        lines = open(self.filename, 'r').readlines()
        self.entries = []
        for line in lines:
            res=line.split('/')
            if len(res)==1:
                entry=[res[0].rstrip(),None]
            else:
                username, passwd = res
                entry = [username, passwd.rstrip()]

            self.entries.append(entry)

    def save(self):
        """Write the htpasswd file to disk"""
        open(self.filename, 'w').writelines(["%s/%s\n" % (entry[0], entry[1])
                                             for entry in self.entries])

    def update(self, username, password):
        """Replace the entry for the given user, or add it if new."""
        matching_entries = [entry for entry in self.entries
                            if entry[0] == username]
        if matching_entries:
            matching_entries[0][1] = password
        else:
            self.entries.append([username, password])

    def delete(self, username):
        """Remove the entry for the given user."""
        self.entries = [entry for entry in self.entries
                        if entry[0] != username]


def main1():
    """%prog [-c] -b filename username password
    Create or update an htpasswd file"""
    # For now, we only care about the use cases that affect tests/functional.py
    parser = OptionParser(usage=main.__doc__)
    parser.add_option('-b', action='store_true', dest='batch', default=False,
        help='Batch mode; password is passed on the command line IN THE CLEAR.'
        )
    parser.add_option('-c', action='store_true', dest='create', default=False,
        help='Create a new htpasswd file, overwriting any existing file.')
    parser.add_option('-D', action='store_true', dest='delete_user',
        default=False, help='Remove the given user from the password file.')

    options, args = parser.parse_args()

    def syntax_error(msg):
        """Utility function for displaying fatal error messages with usage
        help.
        """
        sys.stderr.write("Syntax error: " + msg)
        sys.stderr.write(parser.get_usage())
        sys.exit(1)

    if not options.batch:
        syntax_error("Only batch mode is supported\n")

    # Non-option arguments
    if len(args) < 2:
        syntax_error("Insufficient number of arguments.\n")
    filename, username = args[:2]
    if options.delete_user:
        if len(args) != 2:
            syntax_error("Incorrect number of arguments.\n")
        password = None
    else:
        if len(args) != 3:
            syntax_error("Incorrect number of arguments.\n")
        password = args[2]

    passwdfile = HtpasswdFile(filename, create=options.create)

    if options.delete_user:
        passwdfile.delete(username)
    else:
        passwdfile.update(username, password)

    passwdfile.save()


def main():
    """%prog [-c -r] -b filename
    Create or update an htpasswd file for list of users
    > filename - users list filename
    """
    
    parser = OptionParser(usage=main.__doc__)

    parser.add_option('-c', action='store_true', dest='create', default=False,
        help='Create a new htpasswd file, overwriting any existing file.')
    parser.add_option('-D', action='store_true', dest='delete_user',
        default=False, help='Remove the given user from the password file.')
    parser.add_option('-r', action='store_true', dest='regenerate', default=False,
        help='Regenerates users list file passwords.')

    options, args = parser.parse_args()

    def syntax_error(msg):
        """Utility function for displaying fatal error messages with usage
        help.
        """
        sys.stderr.write("Syntax error: " + msg)
        sys.stderr.write(parser.get_usage())
        sys.exit(1)

    if len(args) < 1:
        syntax_error("Insufficient number of arguments.\n")
    filename = args[0]

    
    usersfile = UsersFile(filename, create=options.create)
    print usersfile.entries
    
    for entry in usersfile.entries:
        if options.regenerate or entry[1] is None or entry[1]=='' or entry[1]=='None':
            entry[1]=makepasswd1()

    print usersfile.entries
    
    usersfile.save()
    
    passwdfile = HtpasswdFile("htpasswd", create=True)
    
    for (username, password) in usersfile.entries:
        passwdfile.update(username, password)
    
    passwdfile.save()
    
if __name__ == '__main__':
    main()
    
