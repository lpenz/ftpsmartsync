#!/usr/bin/env python3
#
# Copyright (C) 2009 Leandro Lisboa Penz <lpenz@lpenz.org>
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.
"""Tests for ftpsmartsync"""

import os
import unittest
import tempfile
import shutil
import logging
import socket

import threading

try:
    import Queue as queue
except ImportError:
    import queue

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import ftpsmartsync

logging.basicConfig(format="%(asctime)s %(name)s %(message)s", level=logging.DEBUG)


class FtpServer:
    def __init__(self, path, user, secret, port):
        self.path = path
        self.user = user
        self.secret = secret
        self.port = port
        self.log = logging.getLogger(str(self.__class__))
        self.sockfd = None
        self.thread = None
        self.server = None
        self.quit_event = threading.Event()
        self.exc_queue = queue.Queue()

    @staticmethod
    def threadfunction(quit_event, exc_queue, server):
        log = logging.getLogger("ftpthread")
        try:
            while not quit_event.isSet():
                log.info("calling server.serve_forever")
                server.serve_forever(timeout=1, blocking=True)
        except Exception as e:
            exc_queue.put(e)
        else:
            exc_queue.put(None)

    def start(self):
        authorizer = DummyAuthorizer()
        authorizer.add_user(self.user, self.secret, self.path, perm="elradfmwM")
        # authorizer.add_anonymous("/home/nobody")
        handler = FTPHandler
        handler.authorizer = authorizer
        self.sockfd = socket.socket()
        self.sockfd.bind(("127.0.0.1", self.port))
        self.server = FTPServer(self.sockfd, handler)
        args = (self.quit_event, self.exc_queue, self.server)
        self.thread = threading.Thread(target=FtpServer.threadfunction, args=args)
        self.log.info("starting thread")
        self.thread.start()

    def close(self):
        self.log.info("FTPServer: closing")
        self.log.info("quit_event.set")
        self.quit_event.set()
        self.log.info("server.close")
        self.server.close()
        self.log.info("thread.join")
        self.thread.join()
        self.log.info("sockfd.close")
        self.sockfd.close()
        exc = self.exc_queue.get()
        if exc:
            raise exc


class TestsFtpsmartsyncBase(object):
    def setUp(self):
        self.log = logging.getLogger(str(self.__class__))
        self.srcpath = tempfile.mkdtemp()
        self.dstpath = tempfile.mkdtemp()
        self.user = "user"
        self.secret = "secret"
        self.port = 2121
        self.ftpserver = FtpServer(self.dstpath, self.user, self.secret, self.port)
        self.ftpserver.start()

    def tearDown(self):
        self.log.info("tearing down")
        try:
            self.ftpserver.close()
        finally:
            shutil.rmtree(self.srcpath)
            shutil.rmtree(self.dstpath)


class TestsBasic(unittest.TestCase):
    def testLocalHashes(self):
        path = tempfile.mkdtemp()
        try:
            with open(os.path.join(path, "test.txt"), "w") as fd:
                fd.write("test.txt")
            files, hashes = ftpsmartsync.localFilesGet(path)
            assert len(files)
            assert "test.txt" in files
            assert len(hashes)
            assert "test.txt" in hashes
        finally:
            shutil.rmtree(path)


class TestsFtpsmartsync(TestsFtpsmartsyncBase, unittest.TestCase):
    def setUp(self):
        TestsFtpsmartsyncBase.setUp(self)
        with open(os.path.join(self.srcpath, ".ftp_upstream"), "w") as fd:
            fd.write("ftp://{}@127.0.0.1:{}/\n".format(self.user, self.port))
        with open(os.path.join(self.srcpath, "myfile1.txt"), "w") as fd:
            fd.write("myfile1.txt")
        with open(os.path.join(self.srcpath, "myfile2.txt"), "w") as fd:
            fd.write("myfile2.txt")
        with open(os.path.expanduser("~/.netrc"), "w") as fd:
            os.fchmod(fd.fileno(), 0o600)
            fd.write("machine 127.0.0.1\n")
            fd.write("login {}\n".format(self.user))
            fd.write("password {}\n".format(self.secret))

    def tearDown(self):
        TestsFtpsmartsyncBase.tearDown(self)
        os.unlink(os.path.expanduser("~/.netrc"))

    def test_ftpupstream(self):
        self.log.warning("src %s, dst %s", self.srcpath, self.dstpath)
        _, local = ftpsmartsync.localFilesGet(self.srcpath)
        self.log.warning("src %s = %d", self.srcpath, len(local))
        ftpsmartsync.ftpsmartsync(self.srcpath)
        self.maxDiff = None
        _, remote = ftpsmartsync.localFilesGet(self.dstpath)
        remote.pop("hashes.txt", None)
        self.log.warning("dst %s = %d", self.dstpath, len(remote))
        self.assertEqual(local, remote)


if __name__ == "__main__":
    unittest.main()
