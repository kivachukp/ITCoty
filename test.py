from _apps.endpoints.predictive_method2 import Predictive
from _apps.endpoints import endpoints
from helper_functions.database_update_data.database_update import DatabaseUpdate


# update = DatabaseUpdate()
# update.update_id()

endpoints.run_endpoints()

# cur.execute(
#     'SELECT tbl_users.tbluserid, CONCAT(firstname,\' \', middle_initial, \' \', lastname) AS \"FULL NAME\", tbl_single_role.userrole, image_path, tbl_single_role.tblsingleroleid FROM tbl_users INNER JOIN tbl_single_role ON tbl_users.tblsingleroleid = tbl_single_role.tblsingleroleid  WHERE tbl_users.tblsingleroleid < 4 ORDER BY tbluserid ASC LIMIT {limit} offset {offset}'.format(
#         limit=10, offset=(5 * int(page))))
# data = cur.fetchall()
#
# pagination = Pagination(page=page, total=data2, css_framework='bootstrap4', record_name='users')
#
# return render_template('tables.html', data=data, pagination=pagination)