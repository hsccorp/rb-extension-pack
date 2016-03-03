# This file handles the request from UI to get the detailed list of all review
# for a given project in a given duration.
#
# It connects to the MySQL DB and returns the JSON formatted data to the 
# frontend.

from reviewboard.webapi.base import WebAPIResource
import logging
import MySQLdb
import json
import ast
import datetime

DB_IP = "127.0.0.1"
DB_PORT = 3306
USER = "root"
PASSWD = "hsc321"
DB_NAME = "reviewboard"

# For data received from DB
data = []

class HscReportResource(WebAPIResource):
    """HscReports class return hsc excel format."""
    # name in web api link.
    name = 'hsc_report'

    # name in api request.
    uri_name = 'report'

    # methods allowed for this resource.
    allowed_methods = ('GET', 'POST')
    logging.debug("Hello HSC Reports")

    # GET request handling.
    def get_list(self, request, *args, **kwargs):

        logging.debug(request.GET['review_group'])
        logging.debug(request.GET['start_date'])
        logging.debug(request.GET['end_date'])
        logging.debug("GET: Hello HSC")
        reviewGroup = request.GET['review_group']
        startDate = request.GET['start_date']
        endDate = request.GET['end_date']
        return 200, {self.item_result_key: self.get_rvw_summary_date(reviewGroup, startDate, endDate)}

    # POST request handling.
    def create(self, request, api_format, *args, **kwargs):
        logging.debug("POST: Hello HSC")
        return 200, {self.item_result_key: {'name': 'vinay kumar'}}

    def get_rvw_summary_date(self, reviewGroup, fromTime, toTime):
        # Add a day to the toTime. This is required so that when viewing report
        # on 4-Nov, the reviews posted on 4-Nov are also visible in the report
        toTime = (datetime.datetime.strptime(toTime, '%Y-%m-%d')+ datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        query = "select au.first_name,au.last_name,rr.summary,rr.description,rr.id,rr.issue_open_count,rr.issue_resolved_count,rr.issue_dropped_count,rc.extra_data"\
                " from reviews_reviewrequest rr"\
                " left join reviews_review rev on rr.id = rev.review_request_id"\
                " join auth_user au on rr.submitter_id = au.id"\
                " left join reviews_review_comments rrc on rev.id = rrc.review_id"\
                " left join reviews_comment rc on rrc.comment_id = rc.id"\
                " where rr.repository_id in (select scm_repo.id"\
                                            " from scmtools_repository scm_repo, reviews_group rg, scmtools_repository_review_groups srrg"\
                                            " where rg.id=srrg.group_id"\
                                            " and srrg.repository_id=scm_repo.id"\
                                            " and rg.display_name='" + reviewGroup + "')"\
                " and ((rr.time_added >= '"+fromTime+"'and rr.time_added<= '"+toTime+"') or (rr.last_updated>='"+fromTime+"' and rr.last_updated<='"+toTime+"'))"\
                " and rr.status != 'D'"
        logging.debug(query);

        try:
               # Open database connection
               db = MySQLdb.connect(DB_IP, USER, PASSWD, DB_NAME)

               # prepare a cursor object using cursor() method
               cursor = db.cursor()

               cursor.execute(query)

               # Get all the data and close the connection
               data = cursor.fetchall()
               db.close()
        except MySQLdb.Error as e:
             logging.error("********MySQL Error [%d]: %s" % (e.args[0], e.args[1]))
                
        output = {}
        for row in data:
            if row[4] in output.keys():
                if row[8] is not None:
                    extra_data = ast.literal_eval(row[8])
                    if bool(extra_data) and 'severity' in extra_data:
                        review_sum = output[row[4]]
                        review_sum[extra_data['severity']] = review_sum[extra_data['severity']] + 1
            else:
                review_sum = {}
                review_sum["firstName"] = row[0]
                review_sum["lastName"] = row[1]
                review_sum["summary"] = row[2]
                review_sum["id"] = row[4]
                review_sum['open'] = row[5]
                review_sum['resolved'] = row[6]
                review_sum['dropped'] = row[7]
                review_sum['major'] = 0
                review_sum['minor'] = 0
                review_sum['critical'] = 0
                review_sum['enhancement'] = 0
                if row[8] is not None:
                    extra_data = ast.literal_eval(row[8])
                    if bool(extra_data) and 'severity' in extra_data:
                        review_sum[extra_data['severity']] = review_sum[extra_data['severity']] + 1
                output[row[4]] = review_sum
        return json.dumps(output)


hscreport_resource = HscReportResource()
