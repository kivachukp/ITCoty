from db_operations.scraping_db import DataBaseOperations

db = DataBaseOperations()
# info = db.get_information_about_tables_and_fields()
# print(info)

db.change_type_column(
    list_table_name=['vacancies'],
    name_and_type="profession TYPE VARCHAR (100)"
)