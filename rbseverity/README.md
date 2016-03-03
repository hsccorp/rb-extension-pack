Comment Severity, Category, Defect Cause and Phase Injected Extension
=====================================================================

Overview
--------

This extension provides support for setting the severity level and category of
a comment when commenting on a diff or a file attachment.

The comment dialog has been extended with two drop downs to select the severity
and Category. The values for these are as per the HSC review tracker template.

Severity and category are shown alongside the comments in reviews and in e-mails, and
can be altered in the review dialog.

The extension also provides support to mention the defect cause and phase injected
for a defect while disposing off the comments. These appear as drop downs on the 
commentIssuebar on the review page.


Requirements
------------

This extension requires a particular hook which is not part of the official 
ReviewBoard release yet. A version of ReviewBoard supporting the hook can be
picked from: https://github.com/hsccorp/reviewboard/tree/hsc_2.5.2

If run without the hook, the defect cause and phase injected won't work. Severity and 
category would work.


Status
------

This extension is production-ready.

