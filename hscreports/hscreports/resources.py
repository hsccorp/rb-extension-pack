from reviewboard.webapi.base import WebAPIResource
import logging
import MySQLdb
import json
import ast

DB_IP = "192.168.121.51"
DB_PORT = 3306
USER = "root"
PASSWD = "hsc321"
DB_NAME = "reviewboard_dev"
# Open database connection
db = MySQLdb.connect(DB_IP, USER, PASSWD, DB_NAME)

# prepare a cursor object using cursor() method
cursor = db.cursor()


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
        logging.debug(request.GET['repo'])
        logging.debug(request.GET['start_date'])
        logging.debug(request.GET['end_date'])
        logging.debug("GET: Hello HSC")
        startDate = request.GET['start_date']
        endDate = request.GET['end_date']
        return 200, {self.item_result_key: self.get_rvw_summary_date("HNS-Jupiter-Tools", startDate, endDate)}

    # POST request handling.
    def create(self, request, api_format, *args, **kwargs):
        logging.debug("POST: Hello HSC")
        return 200, {self.item_result_key: {'name': 'vinay kumar'}}

    def get_rvw_summary_date(self, repo_name, fromTime, toTime):

        query = "select au.first_name,au.last_name,rr.summary,rr.description,rr.id,rr.issue_open_count,rr.issue_resolved_count,rr.issue_dropped_count,rc.extra_data"\
                " from reviews_reviewrequest rr"\
                " left join reviews_review rev on rr.id = rev.review_request_id"\
                " join auth_user au on rr.submitter_id = au.id"\
                " left join reviews_review_comments rrc on rev.id = rrc.review_id"\
                " left join reviews_comment rc on rrc.comment_id = rc.id"\
                " where rr.repository_id in (select id from scmtools_repository where name='HNS-Jupiter-Tools')"\
                " and ((rr.time_added >= '"+fromTime+"'and rr.time_added<= '"+toTime+"') or (rr.last_updated>='"+fromTime+"' and rr.last_updated<='"+toTime+"'))"\
                " and rr.status != 'D'"
        print query;

        cursor.execute(query)
        data = cursor.fetchall()

        output = {}
        for row in data:
            if row[4] in output.keys():
                if row[8] is not None:
                    extra_data = ast.literal_eval(row[8])
                    if bool(extra_data):
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
                    if bool(extra_data):
                        review_sum[extra_data['severity']] = review_sum[extra_data['severity']] + 1
                output[row[4]] = review_sum
        return json.dumps(output)


hscreport_resource = HscReportResource()
