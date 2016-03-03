# This file handles the request from UI to get the details for a particular review
#
# It connects to the MySQL DB and returns the data in CSV format to the frontend.
# The data format is similar to the 'Review Log Tracker' of HSC BMS.

from reviewboard.webapi.base import WebAPIResource
import logging
import MySQLdb
import ast
import csv
import io
from datetime import datetime


DB_IP = '127.0.0.1'
DB_PORT = 3306
USER = "<user_name>"
PASSWD = "<password>"
DB_NAME = "<db_name>"

# For data received from DB
data = []


class HscReportResourceExportCsv(WebAPIResource):
    """HscReports class return hsc excel format."""
    # name in web api link.
    name = 'hsc_export_csv'

    # name in api request.
    uri_name = 'export'

    # methods allowed for this resource.
    allowed_methods = ('GET', 'POST')
    logging.debug("Hello HSC Reports")


    #   hardcoded data
    ph_detect = 'Code Review (Internal)'
    ph_inject = ' '
    cause = ' '
    disp_pre = ' '
    fix_in_rev = ' '
    on_rev = ' '

    # Header for the CSV file
    header = ['S.No','Location','Phase Detected','Defect Severity','Description','Disposition (Pre-Meeting)',
              'Disposition (Post-Meeting)','Disposition Comment','Date Approved','Date Closed',
              'Fixed in Revision','Reviewer','Date Created','On Revision','Defect Category','Phase Injected',
              'Defect Cause']

    # GET request handling.
    def get_list(self, request, *args, **kwargs):
        req_id = request.GET['req_id']
        comment_data = self.get_rvw_detail(req_id)
        return 200, {self.item_result_key: {'data': comment_data}}

    # POST request handling.
    def create(self, request, api_format, *args, **kwargs):
        logging.debug("POST: Hello HSC")
        comment_data = self.get_rvw_detail(req_id)
        return 200, {self.item_result_key: {'data': comment_data}}


    # Convert the RB status to HSC report status
    def match_status(self, x):
        return {
            'R': 'Accepted',
            'D': 'Rejected',
        }.get(x, ' ')

    # Convert the RB category to HSC report category
    def match_category(self, x):
        return {
            'std': 'Standards',
            'func': 'Functional',
            'poor': 'Poor Practice',
            'logical': 'Logical',
            'ppt': 'Presetation/Documantation',
            'query': 'Query/Clarification/Recommendation',
        }.get(x, ' ')


    # Convert the RB severity to HSC report severity
    def match_severity(self, x):
        return {
            'critical': 'Critical',
            'major': 'Major',
            'minor': 'Minor',
            'enhancement': 'Enhancement',
        }.get(x, ' ')


    # Convert the RB cause to HSC BMS template
    def match_cause(self, x):
        return {
            'requirement': 'Ambigous Requirements',
            'design': 'Design Error',
            'stdfollow': 'Standards not followed',
            'stdupd': 'Standards needs updation',
            'knowledge': 'Lack of Knowledge',
            'oversight': 'Oversight',
            'dataerr': 'Data Error',
            'config': 'Incorrect Configuration',
            'hardware': 'Hardware Issue',
            'trace': 'Traceability Not followed',
        }.get(x, ' ')


    # Convert the RB phase injected to HSC BMS values
    def match_phase_injected(self, x):
        return {
            'reqmt': 'Requirement',
            'design': 'Design',
            'code': 'Coding',
            'test': 'Testing',
        }.get(x, ' ')

    #Fetch details for the given request Id of the given repository
    #   Arguments:
    #       rvwId:(number) 
    #   Return:
    #       CSV formatted string
    #
    def get_rvw_detail(self, rvwId):

        try:
            csv_output = io.BytesIO()
            writer = csv.writer(csv_output)

            # Query to get the meta info of the review
            meta_info_query = "select rr.summary, rr.time_added, au.first_name, au.last_name, scm.name "\
                            " from reviews_reviewrequest rr, auth_user au, scmtools_tool scm, scmtools_repository scm_repo "\
                            " where rr.submitter_id=au.id and rr.id=" + str(rvwId) + " and rr.repository_id=scm_repo.id "\
                            " and scm_repo.tool_id=scm.id"

            logging.debug("meta_info_query:%s",meta_info_query)

            # Open database connection
            db = MySQLdb.connect(DB_IP, USER, PASSWD, DB_NAME)

            # prepare a cursor object using cursor() method
            cursor = db.cursor()

            cursor.execute(meta_info_query)
            metadata = cursor.fetchall()

            # Write meta info to the buffer in CSV format
            writer.writerow(["Review Title", metadata[0][0]])
            writer.writerow(["Author name", metadata[0][2] + " " + metadata[0][3]])
            writer.writerow(["Review Initiation Date", metadata[0][1].strftime('%m/%d/%Y')])
            repo_type = metadata[0][4]
            logging.debug("repo type:%s",repo_type)


            # Query to get the reviewers
            reviewer_info_query = "select DISTINCT au.email "\
                                  "from reviews_reviewrequest rr, reviews_reviewrequest_target_groups tg, "\
                                    "reviews_group_users gu, auth_user au, reviews_reviewrequest_target_people tp "\
                                  "where rr.id=" + str(rvwId) + " and "\
                                    "((tg.reviewrequest_id=rr.id and gu.group_id=tg.group_id and au.id=gu.user_id) or "\
                                    "(tp.reviewrequest_id=rr.id and tp.user_id=au.id))"

            # prepare a cursor object using cursor() method
            cursor = db.cursor()
            cursor.execute(reviewer_info_query)
            reviewer_data = cursor.fetchall()

            reviewer_list = ''
            for list in reviewer_data:
                reviewer_list += list[0] + ','
            writer.writerow(["Target Reviewers", reviewer_list])

            # Query to get the number of file diffset and their timestamps
            # If num > 1, reviewee has uploaded a new diff.
            filediffset_query = "select timestamp from diffviewer_diffset where history_id=" + str(rvwId)

            cursor.execute(filediffset_query)
            data = cursor.fetchall()

            comment_fix_dtm = None
            if len(data) > 1:
                comment_fix_dtm = data[len(data)-1]

            # Query to get the ship time and date
            ship_info_query = "select timestamp from reviews_review where ship_it=1 and review_request_id=" + str(rvwId)

            cursor.execute(ship_info_query)
            data = cursor.fetchall()

            ship_dtm = None
            if len(data) > 0:
                ship_dtm = data[len(data)-1]

            # Query to get the diff revision information of the review
            rev_info_query = "select rr.id as rid, ds.id as did, ds.revision, fd.id as fid, fd.dest_file, fd.dest_detail \
                              from reviews_reviewrequest rr, diffviewer_diffset ds, diffviewer_filediff fd \
                              where ds.id=fd.diffset_id \
                              and rr.diffset_history_id=ds.history_id \
                              and rr.id=" + str(rvwId)

            cursor.execute(rev_info_query)
            rev_data = cursor.fetchall()

            # To safe-guard against any indexing errors
            try:
                if len(rev_data) > 1:
                    if repo_type == 'Subversion':
                        # Get the last one and strip the () chars
                        self.fix_in_rev = rev_data[len(rev_data)-1][5][1:-1]
                    elif repo_type == 'ClearCase': 
                        # Get the last one and get the version info
                        file_name = rev_data[len(rev_data)-1][4]
                        version_info_index = file_name.rfind('@') + 1
                        self.fix_in_rev = file_name[version_info_index:]
                    elif repo_type == 'Git': 
                        self.fix_in_rev = rev_data[len(rev_data)-1][5]
                    else:
                        logging.error('Unsupported repo type:%s',repo_type)
            except Exception as e:
                logging.error("********Error [%d]: %s" % (e.args[0], e.args[1]))
                self.fix_in_rev = ' '

            # repo specific query conditions
            # In case of SVN, fetch the dest_detail


            # Query to get all the comments for this review
            all_data_query = "select reviews_comment.id, au.first_name, au.last_name, \
                                   reviews_comment.text, reviews_comment.issue_opened, \
                                   reviews_comment.issue_status, reviews_comment.reply_to_id, reviews_comment.extra_data, \
                                   reviews_comment.first_line, reviews_comment.num_lines, reviews_comment.timestamp, \
                                   diffviewer_filediff.dest_file, diffviewer_filediff.dest_detail \
                                   from ((((((reviews_review \
                                   left join reviews_reviewrequest \
                                   on reviews_review.review_request_id = reviews_reviewrequest.id) \
                                   left join auth_user \
                                   on auth_user.id = reviews_reviewrequest.submitter_id) \
                                   left join reviews_review_comments \
                                   on reviews_review.id = reviews_review_comments.review_id) \
                                   left join reviews_comment \
                                   on reviews_review_comments.comment_id = reviews_comment.id) \
                                   left join auth_user au \
                                   on au.id = reviews_review.user_id) \
                                   left join diffviewer_filediff \
                                   on diffviewer_filediff.id = reviews_comment.filediff_id) \
                                   where reviews_review.review_request_id = " + str(rvwId)

            cursor.execute(all_data_query)
            data = cursor.fetchall()
            db.close()

            # Write table header to the buffer in CSV format
            writer.writerow(self.header)
        except MySQLdb.Error as e:
             logging.error("********MySQL Error [%d]: %s" % (e.args[0], e.args[1]))

        all_data={}
        comment_count = 1;
        for id, rvwr_fname, rvwr_lname, txt, is_issue, status, reply_id, ext_data, first_line, num_lines, ts, file, version in data:
            logging.debug("txt:%s, file:%s, version:%s",txt,file,version)
            if is_issue:
                comment_data = {}
                comment_data['num'] = comment_count

                # Set the file name and On revision
                if repo_type == 'Subversion':
                    # Get the last one and strip the () chars
                    comment_data['on_rev'] = version[1:-1]
                elif repo_type == 'ClearCase': 
                    # Get the last one and get the version info
                    version_info_index = file.rfind('@')
                    comment_data['on_rev'] = file[version_info_index + 1:]
                    file = file[:version_info_index - 1]
                elif repo_type == 'Git': 
                    comment_data['on_rev'] = version
                else:
                    logging.error('Unsupported repotype:%s',repo_type)

                comment_data['loc'] = file + ':' + str(first_line)
                if num_lines > 1:
                    comment_data['loc'] += '-' + str(first_line+num_lines-1)
                comment_data['reviewer'] = rvwr_fname + ' ' + rvwr_lname
                ext_data_dic = ast.literal_eval(ext_data)
                if 'severity' in ext_data_dic:
                    comment_data['severity'] = self.match_severity(ext_data_dic["severity"])
                else:
                    comment_data['severity'] = ' ';
                if 'category' in ext_data_dic:
                    comment_data['category'] = self.match_category(ext_data_dic["category"])
                else:
                    comment_data['category'] = ' ';
                if 'cause' in ext_data_dic:
                    comment_data['cause'] = self.match_cause(ext_data_dic["cause"])
                else:
                    comment_data['cause'] = ' ';
                if 'phase' in ext_data_dic:
                    comment_data['ph_inject'] = self.match_phase_injected(ext_data_dic["phase"])
                else:
                    comment_data['ph_inject'] = ' ';
                comment_data['desc'] = txt
                comment_data['disp'] = self.match_status(status)
                comment_data['create_dtm'] = ts.strftime('%m/%d/%Y')
                comment_data['disp_txt'] = ''
                all_data[str(id)] = comment_data
                if comment_fix_dtm is not None:
                    comment_data['fix_date'] = comment_fix_dtm[0].strftime('%m/%d/%Y')
                else:
                    comment_data['fix_date'] = ' '
                if ship_dtm is not None:
                    comment_data['approve_date'] = ship_dtm[0].strftime('%m/%d/%Y')
                else:
                    comment_data['approve_date'] = ' '

                comment_count = comment_count + 1
            else:
                if str(reply_id) in all_data:
                    if (all_data[str(reply_id)]['disp_txt'] == ''):
                        all_data[str(reply_id)]['disp_txt'] = rvwr_fname + ' ' + rvwr_lname + ': ' + txt
                    else:
                        # Append the reviewer name and his/her comment
                        all_data[str(reply_id)]['disp_txt'] = all_data[str(reply_id)]['disp_txt'] + \
                                                             '\n' + \
                                                             rvwr_fname + ' ' + rvwr_lname + ': ' + txt
                    all_data[str(reply_id)]['fix_date'] = ts.strftime('%m/%d/%Y')


        # Write table contents to the buffer in CSV format
        for row in sorted(all_data):
            writer.writerow([all_data[row]['num'], all_data[row]['loc'], self.ph_detect, all_data[row]['severity'], 
                             all_data[row]['desc'], self.disp_pre, all_data[row]['disp'], all_data[row]['disp_txt'],
                             all_data[row]['approve_date'], all_data[row]['fix_date'], self.fix_in_rev, all_data[row]['reviewer'],
                             all_data[row]['create_dtm'], all_data[row]['on_rev'], all_data[row]['category'], all_data[row]['ph_inject'], all_data[row]['cause']])

        return csv_output.getvalue()


hscreport_resource_export_csv = HscReportResourceExportCsv()
