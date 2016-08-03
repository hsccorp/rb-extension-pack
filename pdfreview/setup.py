#!/usr/bin/env python
from reviewboard.extensions.packaging import setup


PACKAGE = "pdfreview"
VERSION = "0.1"

setup(
    name=PACKAGE,
    version=VERSION,
    description="Extension for ReviewBoard with support to review PDF documents",
    author="Hughes Systique Corporation",
    author_email="viney.yadav@hsc.com",
    url='http://hsc.com/',
    download_url='',
    packages=["pdfreview"], 
    entry_points={
        'reviewboard.extensions':
            ['pdfreview = pdfreview.extension:PDFReviewUIExtension',]
    },
    package_data={
        'pdfreview_extension': [
            'static/css/*.css',
            'static/js/*.js',
            'templates/pdfreview/*.html',
            'templates/pdfreview/*.txt',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Review Board',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
