[![Build Status](https://travis-ci.org/lpenz/ftpsmartsync.png?branch=master)](https://travis-ci.org/lpenz/ftpsmartsync)
[![codecov](https://codecov.io/gh/lpenz/ftpsmartsync/branch/master/graph/badge.svg)](https://codecov.io/gh/lpenz/ftpsmartsync)
[![PyPI version](https://badge.fury.io/py/ftpsmartsync.svg)](https://badge.fury.io/py/ftpsmartsync)


ftpsmartsync
=======


# About

ftpsmartsync is a program that synchronizes all files beneath the current
directory with an FTP host efficiently.

The destination host is identified by a *.ftp\_upstream* in the current
directory that must have the following line:

    ftp://user@host/path

The password is found by looking at `~/.netrc`, see **netrc**(5). If
netrc is unavailable, then gnome-keyring is used. For more information
about gnome-keyring, please refer to
<http://wiki.github.com/xrogaan/ftpsync/>

ftpsmartsync sends all files in the current directory to the target host, and
stores the MD5 of the sent files in a *hashes.txt* files in the remote
host. When syncing again, it checks the MD5 of each file against the one
stored in the remote *hashes.txt* file, and only sends the files that
are different. This makes ftpsmartsync very efficient when synchronizing a
directory with only a few different files, as long as they are always
sent by ftpsmartsync.


# Options

**-h** Help.

**-q** Quiet mode.

**-s** Safe mode: sends hashes.txt after every successful file transfer.


# Authors

Originaly written by [Leandro Penz](http://lpenz.github.com)

gnome-keyring and fixes by [Bellière Ludovic](http://github.com/xrogaan)

