import logging
import os
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import ReviewUIHook
from reviewboard.reviews.ui.base import FileAttachmentReviewUI
from PyPDF2 import PdfFileWriter, PdfFileReader
from PythonMagick import Image
from reviewboard.settings import MEDIA_ROOT
from django.utils.html import escape
from reviewboard.attachments.mimetypes import register_mimetype_handler, MimetypeHandler
from django.utils.safestring import mark_safe


class PDFReviewUI(FileAttachmentReviewUI):
    """ReviewUI for PDF mimetypes"""
    name = 'PDF'
    supported_mimetypes = ['application/pdf']
    # template_name = 'pdfreview/pdfreview.html'
    css_bundles = ['pdfreviewable']
    js_bundles = ['pdfreviewable']

    js_model_class = 'PDFReviewable'
    js_view_class = 'PDFReviewableView'

    def get_js_model_data(self):
        data = super(PDFReviewUI, self).get_js_model_data()
        data['pdfURL'] = self.obj.file.url
        return data

    def serialize_comments(self, comments):
        result = {}
        serialized_comments = \
            super(PDFReviewUI, self).serialize_comments(comments)

        for serialized_comment in serialized_comments:
            try:
                position = '%(x)sx%(y)s+%(width)s+%(height)s' \
                           % serialized_comment
            except KeyError:
                # It's possible this comment was made before the review UI
                # was provided, meaning it has no data. If this is the case,
                # ignore this particular comment, since it doesn't have a
                # region.
                continue

            result.setdefault(position, []).append(serialized_comment)

        return result

    def get_comment_thumbnail(self, comment):
        try:
            x = int(comment.extra_data['x'])
            y = int(comment.extra_data['y'])
            width = int(comment.extra_data['width'])
            height = int(comment.extra_data['height'])
        except (KeyError, ValueError):
            # This may be a comment from before we had review UIs. Or,
            # corrupted data. Either way, don't display anything.
            return None

        logging.error(" working:")
        file_path = os.path.join(MEDIA_ROOT, comment.file_attachment.file.name)
        storage = comment.file_attachment.file.storage
        basename = file_path

        new_name = '%s_%d_%d_%d_%d.png' % (basename, x, y, width, height)
        new_name1 = '%s_%d_%d_%d_%d.png' % (comment.file_attachment.file.name, x, y, width, height)
        if not storage.exists(new_name):
            try:
                input1 = PdfFileReader(file(file_path, "rb"))
                output = PdfFileWriter()
                numpages = input1.getNumPages()
                i=0
                page_height=0
                y1=0
                page_height1 = 0
                for i in range(0, numpages):
                    page = input1.getPage(i)
                    page_height = page.mediaBox.getHeight() + 1.3
                    page_height *= 1.5
                    page_height1 += page_height
                    if y <= page_height1:
                        pageno = i
                        page_height1 -= page_height
                        y1 = y - page_height1
                        break
                page = input1.getPage(pageno)
                page.scale(1.5, 1.5)

                page.cropBox.lowerLeft = (x, page_height - (y1 + height))
                page.cropBox.upperRight = (x + width, page_height - y1)

                output.addPage(page)
                page = output.getPage(0)
                page.mediaBox.lowerLeft = (x, page_height - (y1 + height))
                page.mediaBox.upperRight = (x + width, page_height - y1)

                output_stream = file("out.pdf", "wb")
                output.write(output_stream)
                output_stream.close()
                im = Image('out.pdf')
                im.quality(100)
                im.magick('PNG')

                im.write(str(new_name))

            except (IOError, KeyError) as e:
                logging.error('Error cropping image file %s at %d, %d, %d, %d '
                              'and saving as %s: %s' %
                              (file_path, x, y, width, height, new_name, e),
                              exc_info=1)
                return ""

        pdf_url = storage.url(new_name1)

        pdf_html = (
            '<img class="modified-image" src="%s" width="%s" height="%s" '
            'alt="%s" />'
            % (pdf_url, width, height, escape(comment.text)))
        logging.error("pdf html :")
        logging.error(pdf_html)

        return pdf_html


class PDFMimetype(MimetypeHandler):
    """Handles image mimetypes."""

    supported_mimetypes = ['application/pdf']

    def get_thumbnail(self):
        """Return a thumbnail of the image."""
        file_path1 = os.path.join(MEDIA_ROOT, self.attachment.file.name)
        storage1 = self.attachment.file.storage
        basename1 = file_path1
        new_name2 = '%s_%d.png' % (basename1, 300)
        new_name3 = '%s_%d.png' % (self.attachment.file.name, 300)
        if not storage1.exists(new_name2):
            try:
                input1 = PdfFileReader(file(file_path1, "rb"))
                output = PdfFileWriter()
                page = input1.getPage(0)
                page.scale(1.5, 1.5)
                output.addPage(page)
                page = output.getPage(0)
                output_stream = file("out.pdf", "wb")
                output.write(output_stream)
                output_stream.close()
                im = Image('out.pdf')
                im.quality(100)
                im.magick('PNG')
                im.write(str(new_name2))

            except (IOError, KeyError) as e:
                return ""

        pdf_url = storage1.url(new_name3)

        return mark_safe(
            '<div class="file-thumbnail">'
            '<img src="%s" alt="%s" style="width:300px;" />'
            '</div>'
            % (pdf_url,
               escape(self.attachment.caption)))


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
        register_mimetype_handler(PDFMimetype)
