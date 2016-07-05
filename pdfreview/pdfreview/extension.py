from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import ReviewUIHook
from reviewboard.reviews.ui.base import FileAttachmentReviewUI
from django.utils.encoding import force_unicode
#import pygments
#import logging
class PDFReviewUI(FileAttachmentReviewUI):
    """ReviewUI for PDF mimetypes"""
    name = 'PDF'
    supported_mimetypes = ['application/pdf']
    #template_name = 'pdf/pdf.html'


    css_bundles = ['pdfreviewable']
    js_bundles = ['pdfreviewable']

    js_model_class = 'PDFReviewable'
    js_view_class = 'PDFReviewableView'
	
    def get_js_model_data(self):
        data = super(PDFReviewUI, self).get_js_model_data()
        data['pdfURL'] = self.obj.file.url
        return data

	
class PDFReviewUIExtension(Extension):
    css_bundles = {
        'default': {
            'source_filenames': ['css/pdfreviewable.css'],
        },
    }

    js_bundles = {
        'default': {
            'source_filenames': [
                'js/models/pdfReviewableModel.js',
                'js/views/pdfReviewableView.js',
				'js/lib/pdf.js',
				'js/lib/pdf.worker.js'
            ],
        },
    }

    def initialize(self):
        ReviewUIHook(self, [PDFReviewUI])








