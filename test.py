
from helper_functions.database_update_data.database_update_data import DatabaseUpdateData
#
update = DatabaseUpdateData()
update.create_table('vacancies')
update.update_id('vacancies')
