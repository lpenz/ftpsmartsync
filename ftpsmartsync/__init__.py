# Copyright (C) 2009 Leandro Lisboa Penz <lpenz@lpenz.org>
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

"""A tool to synchronize the current directory remotly using FTP."""

import sys
import os
try:
    import gnomekeyring
    from getpass import getpass
except ImportError:
    gtkpresence = False
else:
    gtkpresence = True

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from netrc import netrc
import ftplib
import hashlib
import re
from tempfile import TemporaryFile
import socket
import random
import logging

PROGRAM_NAME = "ftpsmartsync"
PROGRAM_VERSION = "1.4"

__version__ = PROGRAM_VERSION

HASHFILENAME = 'hashes.txt'

# Useful functions: ##########################################################


def uptime():
    '''Uptime used as a monotonic clock.'''
    uptfile = open('/proc/uptime')
    upt = uptfile.read().split('.')[0]
    uptfile.close()
    return int(upt)


def _log():
    if not _log.logger:
        _log.logger = logging.getLogger(__name__)
    return _log.logger


_log.logger = None

# Main Ftp class: ############################################################


class Ftp():
    def __init__(self, user, host, port, path):
        self.user = user
        self.host = host
        self.port = port
        self.path = path
        self.hashespending = False
        self.connect()

    def connect(self):
        try:
            auth = netrc().authenticators(self.host)
            # TODO check if the host exists in netrc
        except IOError as msgio:
            if gtkpresence:
                try:
                    keyring = gnomekeyring.get_default_keyring_sync()
                    keyring_info = gnomekeyring.get_info_sync(keyring)
                    if keyring_info.get_is_locked():
                        keyring_pass = getpass('Enter password to unlock your '
                                               'keychain [%s]: ' % (keyring))
                        try:
                            gnomekeyring.unlock_sync(keyring, keyring_pass)
                        except Exception as msg:
                            sys.stderr.write("\nUnable to unlock your "
                                             "keychain: %s\n" % msg)
                        else:
                            _log().debug("+ [%s] unlocked." % keyring)
                            itempass = gnomekeyring.ITEM_NETWORK_PASSWORD
                            pars = {
                                "server": self.host,
                                "protocol": "ftp",
                                "user": self.user
                            }
                            items = gnomekeyring.find_items_sync(
                                itempass, pars)
                            if len(items) > 0:
                                ftp = ftplib.FTP(self.host, self.user,
                                                 items[0].secret)
                            else:
                                raise Exception('gnomekeyring', 'NoMatchError')
                except gnomekeyring.DeniedError:
                    sys.stderr.write("\nGnome keyring error : "
                                     "Access denied ..\n"
                                     "netrc error: %s\n" % (msgio))
                    sys.exit(1)
                except gnomekeyring.NoMatchError:
                    sys.stderr.write("\nGnome keyring error : "
                                     "No credential for %s..\n"
                                     "netrc error: %s\n" % (self.host, msgio))
                    sys.exit(1)
                except Exception as msg:
                    sys.stderr.write("\nGnome keyring error : %s\n"
                                     "netrc error: %s\n" % (msg, msgio))
                    sys.exit(1)

        else:
            assert self.user == auth[0]
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port)
            ftp.login(auth[0], auth[2])
        try:
            ftp.cwd(self.path)
        except ftplib.error_perm:
            ftp.mkd(self.path)
            ftp.cwd(self.path)
        self.ftp = ftp
        self.dirs = set()

    def sendHashes(self, localHashes):
        if not self.hashespending:
            return
        _log().debug('+ Sending hashes')
        tmpfile = TemporaryFile()
        for f in list(localHashes.keys()):
            tmpfile.write(f.encode('UTF-8'))
            tmpfile.write(' '.encode('UTF-8'))
            tmpfile.write(localHashes[f].encode('UTF-8'))
            tmpfile.write('\n'.encode('UTF-8'))
        tmpfile.seek(0)
        self.ftp.storlines('STOR %s' % HASHFILENAME + '.tmp', tmpfile)
        self.ftp.rename(HASHFILENAME + '.tmp', HASHFILENAME)
        self.hashespending = False

    def mkdir(self, dir):
        if dir == '' or dir in self.dirs:
            return
        self.mkdir(os.path.split(dir)[0])
        try:
            self.ftp.mkd(dir)
        except ftplib.error_perm:
            pass
        self.dirs.add(dir)

    def filesGet(self):
        remoteFiles = set()
        remoteHashes = {}

        def remoteHashesGet(l):
            r = re.compile('^(.+) ([a-f0-9]+)$')
            m = r.match(l)
            remoteFiles.add(m.group(1))
            remoteHashes[m.group(1)] = m.group(2)

        try:
            self.ftp.retrlines('RETR %s' % HASHFILENAME, remoteHashesGet)
        except ftplib.error_perm:
            pass

        return remoteFiles, remoteHashes

    def fileSend(self, filename):
        self.mkdir(os.path.dirname(filename))
        fd = open(filename, 'rb')
        try:
            self.ftp.storbinary('STOR %s' % filename, fd)
            self.hashespending = True
        except socket.error:
            self.connect()
            return False
        except ftplib.error_temp:
            self.connect()
            return False
        return True

    def delete(self, f):
        try:
            self.ftp.delete(f)
            self.hashespending = True
        except ftplib.error_perm:
            pass


# Local files processing: ####################################################


def filesget(filelist, entry):
    assert os.path.exists(entry)
    if os.path.isdir(entry):
        for e in os.listdir(entry):
            filesget(filelist, os.path.join(entry, e))
    else:
        filelist.append(os.path.normpath(entry))
    return filelist


def localFilesGet():
    localHashes = {}

    filelist = filesget([], '././')
    filelist.sort()

    for f in filelist:
        fd = open(f, 'rb')
        h = hashlib.sha1()
        contents = fd.read()
        h.update(contents)
        localHashes[f] = h.hexdigest()

    return set(filelist), localHashes


# Core function: #############################################################


def ftpsmartsync(safe=True):
    ok = True

    try:
        fd = open('.ftp_upstream')
    except IOError:
        sys.stderr.write('.ftp_upstream: file not found\n')
        sys.exit(1)

    o = urlparse(fd.read(), 'ftp')
    if not o.username:
        sys.stderr.write('username not given: %s\n' % o.geturl())
        sys.exit(1)
    # ensure the remote path contain at least a '/'
    remote_path = os.path.normpath(o[2] or '/').strip()
    if remote_path.startswith('//'):
        remote_path = remote_path[1:]
    assert remote_path.startswith('/'), repr(remote_path)

    upstreamurl = o.geturl()
    if upstreamurl.endswith('\n'):
        upstreamurl = upstreamurl[:-1]

    _log().debug('+ Upstream is %s' % upstreamurl)
    ftp = Ftp(o.username, o.hostname, o.port, remote_path)
    _log().debug('+ Connected')

    localFiles, localHashes = localFilesGet()
    _log().debug('+ Got %d local hashes' % len(localFiles))

    remoteFiles, remoteHashes = ftp.filesGet()
    _log().debug('+ Got %d remote hashes' % len(remoteFiles))

    _log().debug('+ Deleting remote files')
    todel = remoteFiles.difference(localFiles)
    j = 1
    jtotal = len(todel)
    for f in todel:
        if f == HASHFILENAME:
            continue
        ftp.delete(f)
        _log().debug('+ %4d/%-4d deleted %s' % (j, jtotal, f))
        remoteFiles.discard(f)
        del remoteHashes[f]
        j = j + 1

    tosend = set()
    okHashes = {}

    for f in localFiles:
        if f not in remoteFiles or localHashes[f] != remoteHashes[f]:
            tosend.add(f)
        else:
            okHashes[f] = remoteHashes[f]

    ftp.sendHashes(okHashes)

    _log().debug('+ Sending files')
    sentHashes = {}
    i = 0
    itotal = len(tosend)
    lastupt = uptime()
    lastlen = 0
    tosendList = [x for x in tosend]
    random.shuffle(tosendList)
    for f in tosendList:
        i = i + 1
        if f == 'hashes.txt':
            _log().debug('+ %4d/%-4d skipping %s' % (i, itotal, f))
            continue
        _log().debug('+ %4d/%-4d sending %s' % (i, itotal, f))
        if ftp.fileSend(f):
            sentHashes[f] = localHashes[f]
            okHashes[f] = localHashes[f]
        else:
            _log().error('- ERROR sending %s' % (f))
            ok = False
            ftp.sendHashes(okHashes)
        if safe or (len(okHashes) > lastlen and uptime() - lastupt > 30):
            ftp.sendHashes(okHashes)
            lastupt = uptime()
            lastlen = len(okHashes)

    ftp.sendHashes(okHashes)

    _log().info('+ Summary: sent %d files, deleted %d files, '
                '%d files could not be sent' % (len(sentHashes), len(todel),
                                                len(tosend) - len(sentHashes)))

    return ok
