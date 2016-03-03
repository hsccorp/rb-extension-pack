#!/usr/bin/env python

from reviewboard.extensions.packaging import setup


PACKAGE = "hscreports"
VERSION = "0.1"

setup(
    name=PACKAGE,
    version=VERSION,
    description="Extension hscreports",
    author="Viney Yadav",
    packages=["hscreports"],
    entry_points={
        'reviewboard.extensions':
            '%s = hscreports.extension:Hscreports' % PACKAGE,
    },
    package_data={
        'hscreports': [
            'templates/hscreports/*.txt',
            'templates/hscreports/*.html',
        ],
    }
)