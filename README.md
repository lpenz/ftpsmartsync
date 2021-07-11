[![CI](https://github.com/lpenz/ftpsmartsync/actions/workflows/ci.yml/badge.svg)](https://github.com/lpenz/ftpsmartsync/actions/workflows/ci.yml)
[![coveralls](https://coveralls.io/repos/github/lpenz/ftpsmartsync/badge.svg?branch=main)](https://coveralls.io/github/lpenz/ftpsmartsync?branch=main)
[![packagecloud](https://img.shields.io/badge/deb-packagecloud.io-844fec.svg)](https://packagecloud.io/app/lpenz/debian/search?q=ftpsmartsync)


# ftpsmartsync

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


## Authors

Originaly written by [Leandro Penz](http://lpenz.github.com)

gnome-keyring and fixes by [Bellière Ludovic](http://github.com/xrogaan)

