#!/usr/bin/env python3
#
# Copyright (C) 2009 Leandro Lisboa Penz <lpenz@lpenz.org>
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.
'''Tests for ftpsmartsync'''

import os
import unittest
import tempfile
import shutil
import ftplib
import hashlib
import logging

import threading
try:
    import Queue as queue
except ImportError:
    import queue

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import ftpsmartsync

logging.getLogger().setLevel(logging.DEBUG)


def ftpd_threadfunction(quitEv, exc, tmpdir, user, secret, port):
    try:
        authorizer = DummyAuthorizer()
        authorizer.add_user(user, secret, tmpdir, perm="elradfmwM")
        # authorizer.add_anonymous("/home/nobody")
        handler = FTPHandler
        handler.authorizer = authorizer
        server = FTPServer(("127.0.0.1", port), handler)
        while not quitEv.isSet():
            server.serve_forever(timeout=1, blocking=False)
    except Exception as e:
        exc.put(e)
    else:
        exc.put(None)


def dirInfo(top):
    rv = {}
    for root, dirs, files in os.walk(top):
        for name in files:
            fullname = os.path.join(root, name)
            with open(fullname, 'rb') as fd:
                relname = os.path.relpath(fullname, top)
                h = hashlib.sha1()
                h.update(fd.read())
                rv[relname] = h.hexdigest()
    return rv


class TestsFtpsmartsyncBase(object):
    def setUp(self):
        self.ftpdQuitEv = threading.Event()
        self.ftpdExc = queue.Queue()
        self.ftpdDir = tempfile.mkdtemp()
        self.user = 'user'
        self.secret = 'secret'
        self.port = 2121
        args = (self.ftpdQuitEv, self.ftpdExc, self.ftpdDir, self.user,
                self.secret, self.port)
        self.ftpd = threading.Thread(target=ftpd_threadfunction, args=args)
        self.ftpd.start()
        for i in range(10):
            try:
                ftplib.FTP('127.0.0.1', self.user, self.secret)
                break
            except Exception:
                pass

    def tearDown(self):
        self.ftpdQuitEv.set()
        shutil.rmtree(self.ftpdDir)
        exc = self.ftpdExc.get()
        if exc:
            raise exc


class TestsFtpsmartsync(TestsFtpsmartsyncBase, unittest.TestCase):
    def setUp(self):
        TestsFtpsmartsyncBase.setUp(self)
        with open('.ftp_upstream', 'w') as fd:
            fd.write('ftp://{}@127.0.0.1:{}/\n'.format(self.user, self.port))
        with open(os.path.expanduser('~/.netrc'), 'w') as fd:
            os.fchmod(fd.fileno(), 0o600)
            fd.write('machine 127.0.0.1\n')
            fd.write('login {}\n'.format(self.user))
            fd.write('password {}\n'.format(self.secret))

    def tearDown(self):
        os.unlink('.ftp_upstream')
        os.unlink(os.path.expanduser('~/.netrc'))
        TestsFtpsmartsyncBase.tearDown(self)

    def test_ftpupstream(self):
        local = dirInfo('.')
        ftpsmartsync.ftpsmartsync()
        self.maxDiff = None
        remote = dirInfo(self.ftpdDir)
        remote.pop('hashes.txt', None)
        self.assertEqual(local, remote)


if __name__ == '__main__':
    unittest.main()
