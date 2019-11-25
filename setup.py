#!/usr/bin/env python3
#
# Copyright (C) 2009 Leandro Lisboa Penz <lpenz@lpenz.org>
# This file is subject to the terms and conditions defined in
# file 'LICENSE.txt', which is part of this source code package.

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import re


def version_get():
    with open('ftpsmartsync/__init__.py') as fd:
        for line in fd:
            m = re.match('^PROGRAM_VERSION = "(?P<version>[0-9.]+)"',
                         line)
            if m:
                return m.group('version')


setup(name="ftpsmartsync",
      version=version_get(),
      description="Sync local path with FTP remote efficiently "
      "by transmitting only what is necessary",
      author="Leandro Lisboa Penz",
      author_email="lpenz@lpenz.org",
      url="http://github.com/lpenz/ftpsmartsync",
      data_files=[('share/man/man1', ['ftpsmartsync.1'])],
      packages=['ftpsmartsync'],
      scripts=["bin/ftpsmartsync"],
      long_description="""\
ftpsmartsync is a program that synchronizes all files beneath the current
directory with an FTP host efficiently by keeping a remote file with
the hashes of the files sent.
""",
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'License :: OSI Approved :: '
          'GNU General Public License v2 or later (GPLv2+)',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          ],
      license="GPL2")
