import logging
import os
from subprocess import call
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import ReviewUIHook
from reviewboard.reviews.ui.base import FileAttachmentReviewUI
from reviewboard.settings import MEDIA_ROOT
from django.utils.html import escape
from reviewboard.attachments.mimetypes import register_mimetype_handler, MimetypeHandler
from django.utils.safestring import mark_safe
try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
except:
    pass

class PDFReviewUI(FileAttachmentReviewUI):
    """ReviewUI for PDF mimetypes"""
    name = 'PDF'
    supported_mimetypes = ['application/pdf']
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
        """Returns a thumbnail of the comment.

        If the thumbnail does not exist, it is created.
        """
        page_scale = 1.5
        try:
            x = int(comment.extra_data['x'])
            y = int(comment.extra_data['y'])
            width = int(comment.extra_data['width'])
            height = int(comment.extra_data['height'])
        except (KeyError, ValueError):
            # This may be a comment from before we had review UIs. Or,
            # corrupted data. Either way, don't display anything.
            return None

        file_path = os.path.join(MEDIA_ROOT, comment.file_attachment.file.name)
        storage = comment.file_attachment.file.storage

        thumbnail_abs_path = '%s_%d_%d_%d_%d.png' % (file_path, x, y, width, height)
        thumbnail_path = '%s_%d_%d_%d_%d.png' % (comment.file_attachment.file.name, x, y, width, height)

        # If the thumbnail does not exist, create it
        if not storage.exists(thumbnail_abs_path):
            try:
                input1 = PdfFileReader(file(file_path, "rb"))
                output = PdfFileWriter()
                numpages = input1.getNumPages()
                page_height=0
                offset_from_curr_page=0
                offset_from_top = 0
                # Find the page on which the comment was provided.
                # The y value is the offset of the comment from top of first
                # page. Add the page height of each page and find where y lies.
                for i in range(0, numpages):
                    page = input1.getPage(i)
                    # When rendering the page on UI, each page was scaled up by
                    # 50% (refer: static/js/views/pdfReviewableView.js)
                    # Scale the height by same ratio. The canvas element
                    # at UI also has a 1px border. For the top and bottom borders
                    # add 2 to the height.
                    page_height = int(float(page.mediaBox.getHeight()) * page_scale) + 2
                    offset_from_top += page_height
                    if y <= offset_from_top:
                        pageno = i
                        offset_from_top -= page_height
                        # offset_from_top is bottom of the prev page. Get the
                        # offset of the comment from top of this page. Take
                        # care of adding the 1px top border.
                        offset_from_curr_page = y - offset_from_top + 1
                        break
                page = input1.getPage(pageno)
                # Scale the page before cropping
                page.scale(page_scale, page_scale)

                page.cropBox.lowerLeft = (x, int(page_height) - (offset_from_curr_page + height))
                page.cropBox.upperRight = (x + width, int(page_height) - offset_from_curr_page)

                output.addPage(page)
                page = output.getPage(0)
                page.mediaBox.lowerLeft = (x, int(page_height) - (offset_from_curr_page + height))
                page.mediaBox.upperRight = (x + width, int(page_height) - offset_from_curr_page)

                # Save the cropped command pdf as filename_tmp in same folder.
                # Will be deleted after conversion to image.
                output_stream = file(str(thumbnail_abs_path) + '_tmp', "wb")
                output.write(output_stream)
                output_stream.close()

                # Covert to image.
                call(["convert",
                      str(thumbnail_abs_path) + '_tmp',
                      str(thumbnail_abs_path)])
                # Get rid of the temporary PDF file
                os.remove(str(thumbnail_abs_path) + '_tmp')

            except Exception as e:
                logging.error('Error cropping image file %s at %d, %d, %d, %d '
                              'and saving as %s: %s' %
                              (file_path, x, y, width, height, thumbnail_abs_path, e),
                              exc_info=1)
                return ""

        pdf_url = storage.url(thumbnail_path)

        pdf_html = (
            '<img class="modified-image" src="%s" width="%s" height="%s" '
            'alt="%s" />'
            % (pdf_url, width, height, escape(comment.text)))

        return pdf_html


class PDFMimetype(MimetypeHandler):
    """Handles PDF mimetypes."""

    supported_mimetypes = ['application/pdf']

    def get_thumbnail(self):
        """Return a thumbnail of the first page of the PDF document."""
        file_path = os.path.join(MEDIA_ROOT, self.attachment.file.name)
        storage1 = self.attachment.file.storage
        thumbnail_path = '%s_%d.png' % (file_path, 300)
        file_thumbnail_path = '%s_%d.png' % (self.attachment.file.name, 300)
        if not storage1.exists(thumbnail_path):
            try:
                input1 = PdfFileReader(file(file_path, "rb"))
                output = PdfFileWriter()
                page = input1.getPage(0)
                output.addPage(page)
                output_stream = file(str(thumbnail_path) + "_tmp", "wb")
                output.write(output_stream)
                output_stream.close()

                call(["convert", str(thumbnail_path) + "_tmp", str(thumbnail_path)])
                os.remove(str(thumbnail_path) + "_tmp")

            except Exception as e:
                logging.error('Error creating thumbnail for the doc: %s' %
                              e, exc_info=1)
                return ""

        pdf_url = storage1.url(file_thumbnail_path)

        return mark_safe(
            '<div class="file-thumbnail">'
            '<img src="%s" alt="%s" style="width:300px;" />'
            '</div>'
            % (pdf_url,
               escape(self.attachment.caption)))


class PDFReviewUIExtension(Extension):
    """Extends Review Board for reviewing PDF document.

    When creating or updating comments, users will be required to set a
    severity level. This level will appear in the reviews, in e-mails, and
    in the API (through the comment's extra_data).
    """

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
            ],
        },
        'worker': {
            'source_filenames': [
                'js/lib/pdf.worker.js'
            ],
            'output_filename' : 'pdf.worker.js'
        },
    }

    def initialize(self):
        ReviewUIHook(self, [PDFReviewUI])
        register_mimetype_handler(PDFMimetype)
