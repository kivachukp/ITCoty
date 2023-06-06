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
        full_query = f'CREATE VIEW all_without_sort AS {query[:-7]} ORDER BY time_of_public DESC, id DESC;'

        print(full_query)
        if not self.db.con:
            self.db.connect_db()
        cur = self.db.con.cursor()
        with self.db.con:
            cur.execute(full_query)


    def create_table(self):
        query = ''

        for table in valid_professions:
            query_part = f'SELECT {views_fields_for_web} FROM {table}'
            query += f'{query_part} UNION '
            full_query = f'CREATE TABLE all_vacancies_sorted AS {query[:-7]} ORDER BY time_of_public DESC, id DESC;'

        print(full_query)
        if not self.db.con:
            self.db.connect_db()
        cur = self.db.con.cursor()
        with self.db.con:
            cur.execute(full_query)
        print ('TABLE READY')

    def create_table_from_view(self):

        full_query = f'CREATE TABLE all_vacancies_sorted AS VIEW all_vacancies;'

        print(full_query)
        if not self.db.con:
            self.db.connect_db()
            cur = self.db.con.cursor()
            with self.db.con:
                cur.execute(full_query)
            print ('TABLE READY')

    def update_id(self):

        if not self.db.con:
            self.db.connect_db()
        cur = self.db.con.cursor()
        with self.db.con:
            # cur.execute('CREATE SEQUENCE serial_id START 50000;')
            # cur.execute('ALTER TABLE all_vacancies_sorted ADD COLUMN admin_id_new INT NOT NULL INCREMENT, INCREMENT = 50000;')
            cur.execute("UPDATE all_vacancies_sorted SET admin_id = nextval('serial_id');")
