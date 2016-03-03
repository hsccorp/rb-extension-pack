# hscreports Extension for Review Board.

from __future__ import unicode_literals

from reviewboard.extensions.base import Extension
from hscreports.resources import hscreport_resource
from hscreports.resourceExportCsv import hscreport_resource_export_csv
from reviewboard.datagrids.sidebar import (BaseSidebarSection,
                                           SidebarNavItem)
from reviewboard.extensions.hooks import DashboardSidebarItemsHook
from reviewboard.extensions.hooks import TemplateHook
import logging


class Hscreports(Extension):
    metadata = {
        'Name': 'hscreports',
        'Summary': 'Describe your extension here.',
    }
    resources = [hscreport_resource,hscreport_resource_export_csv]

    def initialize(self):
        DashboardSidebarItemsHook(self, [SampleSidebarSection])

    def __init__(self, *args, **kwargs):
        logging.debug("HSC Reports __init__ calling")
        super(Hscreports, self).__init__(*args, **kwargs)
        TemplateHook(self, 'base-scripts-post', 'hscreports/template.html',
                     apply_to='dashboard')


class SampleSidebarSection(BaseSidebarSection):
    label = 'HSC Reports'
    logging.debug("My Link class callinf")

    def get_items(self):
        logging.debug("My Link:get_items calling")
        return [
            SidebarNavItem(label='Project Report',
                           section=self)
        ]
