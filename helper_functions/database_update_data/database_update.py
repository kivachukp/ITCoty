from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import admin_database, valid_professions, archive_database, views_fields_for_web
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters

class DatabaseUpdate:

    def __init__(self):
        self.db = DataBaseOperations()

    def create_view(self):
        query = ''

        for table in valid_professions:
            query_part = f'SELECT {views_fields_for_web} FROM {table}'
            query += f'{query_part} UNION '
        full_query = f'CREATE VIEW all_vacancies AS {query[:-7]} ORDER BY time_of_public DESC, id DESC;'

        print(full_query)
        if not self.db.con:
            self.db.connect_db()
        cur = self.db.con.cursor()
        with self.db.con:
            cur.execute(full_query)


