#!/usr/bin/env python
'''Tests for ftpsync'''

import os
import unittest
import tempfile
import shutil

import threading
try:
    import Queue as queue
except:
    import queue

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import ftpsync


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


class TestsFtpsyncBase(object):
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

    def tearDown(self):
        self.ftpdQuitEv.set()
        shutil.rmtree(self.ftpdDir)
        exc = self.ftpdExc.get()
        if exc:
            raise exc


class TestsFtpsync(TestsFtpsyncBase, unittest.TestCase):
    def setUp(self):
        TestsFtpsyncBase.setUp(self)
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
        TestsFtpsyncBase.tearDown(self)

    def test_ftpupstream(self):
        ftpsync.ftpsync(quiet=False)


if __name__ == '__main__':
    unittest.main()
