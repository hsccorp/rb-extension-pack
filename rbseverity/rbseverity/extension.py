from reviewboard.extensions.base import Extension, JSExtension
from reviewboard.extensions.hooks import CommentDetailDisplayHook
from reviewboard.urls import reviewable_url_names, review_request_url_names

apply_to_url_names = set(reviewable_url_names + review_request_url_names)


class SeverityCommentDetailDisplay(CommentDetailDisplayHook):
    """Adds the severity information to displayed comments.

    This extends the comments in the review dialog and in the e-mails
    to show the selected severity.
    """
    SEVERITY_LABELS = {
        'critical': 'Critical',
        'major': 'Major',
        'minor': 'Minor',
        'enhancement': 'Enhancement',
    }

    CATEGORY_LABELS = {
        'std': 'Standards',
        'func': 'Functional',
        'poor': 'Poor Practice',
        'logical': 'Logical',
        'ppt': 'Presetation/Documantation',
        'query': 'Query/Clarification/Recommendation',
    }

    HTML_EMAIL_COMMON_SEVERITY_CSS = (
        'font-weight: bold;'
        'font-size: 9pt;'
    )

    HTML_EMAIL_SPECIFIC_SEVERITY_CSS = {
        'critical': 'color: #AA0000;',
        'major': 'color: #AA0000;',
        'minor': 'color: #CC5500;',
        'enhancement': 'color: #006600;',
    }

    def render_review_comment_detail(self, comment):
        """Renders the severity of a comment on a review."""
        severity = comment.extra_data.get('severity')
        category = comment.extra_data.get('category')

#        if not severity:
#            return ''

        return ('<p>'
                '<b>Severity: </b>'
                '<span class="comment-severity comment-severity-%s">'
                '%s'
                '</span>'
                '<b>   Category: %s </b>'
                '</p>'
                % (severity, self._get_severity_label(severity),self._get_category_label(category)))


    def render_email_comment_detail(self, comment, is_html):
        """Renders the severity of a comment on an e-mail."""
        severity = comment.extra_data.get('severity')
        category = comment.extra_data.get('category')

#        if not severity:
#            return ''

        if is_html:
            specific_css = self.HTML_EMAIL_SPECIFIC_SEVERITY_CSS.get(
                severity, '')

            return ('<p style=%s> Severity: <span style="%s">%s</span>  Category:%s </p>'
                    % (self.HTML_EMAIL_COMMON_SEVERITY_CSS,
                       specific_css,
                       self._get_severity_label(severity),
                       self._get_category_label(category)))
        else:
            return '[Severity: %s]\n[Category: %s]\n' % self._get_severity_label(severity) % self._get_category_label(category)

    def _get_severity_label(self, severity):
        return self.SEVERITY_LABELS.get(severity, 'Unknown')

    def _get_category_label(self, category):
        return self.CATEGORY_LABELS.get(category, 'Unknown')


class SeverityJSExtension(JSExtension):
    model_class = 'RBSeverity.Extension'
    apply_to = apply_to_url_names


class SeverityExtension(Extension):
    """Extends Review Board with comment severity support.

    When creating or updating comments, users will be required to set a
    severity level. This level will appear in the reviews, in e-mails, and
    in the API (through the comment's extra_data).
    """
    metadata = {
        'Name': 'Comment Severity',
    }

    js_extensions = [SeverityJSExtension]

    css_bundles = {
        'default': {
            'source_filenames': ['css/severity.less'],
            'apply_to': apply_to_url_names,
        }
    }

    js_bundles = {
        'severity-review': {
            'source_filenames': ['js/severity.js'],
            'apply_to': apply_to_url_names,
        }
    }

    def initialize(self):
        SeverityCommentDetailDisplay(self)

