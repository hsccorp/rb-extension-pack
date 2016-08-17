PDF Review Extension
====================

Overview
--------

This extension provides support for reviewing PDF documents. Users can convert their word/ppt etc documents to PDF and use this extension for reviews.

The PDF document review functionality is similar to Image review feature provided by ReviewBoard except the diff viewer. Instead, it provides an option to view different revisions of the document.

The extension uses [PDF.js](https://mozilla.github.io/pdf.js/) for rendering the PDF pages in browser. PDF.js libraries are bundled with this extension.

The extension also uses [PyPDF2](https://github.com/mstamy2/PyPDF2) and [ImageMagick](http://www.imagemagick.org/) for creating thumbnails for the PDF documents and the review comments. If either of these is not installed, the thumbnails won't be available.


Requirements
------------

This extension requires ReviewBoard 2.5 or higher.


Status
------

This extension is under development.
