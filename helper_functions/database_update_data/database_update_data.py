"""
There are all functions for the database updating by new updates anywhere
"""
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import admin_database, valid_professions, archive_database, \
    admin_table_fields, preview_fields_for_web
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters

class DatabaseUpdateData:

    def __init__(self):
        self.db = DataBaseOperations()

    async def update_city_field(self):
        fields = 'id, city'
        responses = self.db.get_all_from_db(
            table_name=admin_database,
            without_sort=True,
            field=fields
        )
        counter = 1
        for response in responses:
            city_and_country = response[1]
            id = response[0]
            if city_and_country:
                city_finder = FinderAddParameters()
                new_city_and_country = await city_finder.find_city_country(city_and_country)
                if new_city_and_country:
                    if new_city_and_country != city_and_country:
                        self.db.push_to_db_common(
                            table_name=admin_database,
                            fields_values_dict={"city": new_city_and_country},
                            params=f"WHERE id={id}",
                        )
                        print(f'{counter}. Field City has been changed\nfrom {city_and_country} to {new_city_and_country}\n----------')
                        pass
                    else:
                        print(f"{counter}. it was correct: {new_city_and_country}\n----------")
                else:
                    print(f'{counter}. Nothing for change\n----------')
                pass
            else:
                print(f'{counter}. city not was in the db\n----------')
            counter += 1

    async def create_salary_fields_usd(self):
        table_list = valid_professions.copy()
        table_list.extend([admin_database, archive_database])

        self.db.add_columns_to_tables(table_list=table_list, column_name_type=[
            "rate REAL",
            "salary_from_usd_month INT",
            "salary_to_usd_month INT",
        ])
        pass

    async def update_salary_fields(self, create_db_structure=True):
        if create_db_structure:
            table_list = valid_professions.copy()
            table_list.extend([admin_database, archive_database])
            self.db.add_columns_to_tables(table_list=table_list, column_name_type=["salary_from INT", "salary_to INT", "salary_currency VARCHAR(20)", "salary_period VARCHAR(50)"])

        responses = self.db.get_all_from_db(
            table_name=admin_database,
            without_sort=True,
            field="id, salary"
        )
        if responses:
            for response in responses:
                id = response[0]
                salary = response[1].split(", ")
                if salary and salary[0] and len(salary)<4:
                    salary = self.finder.salary_to_set_form(text=", ".join(salary))
                    # salary = ", ".join(salary)

                if salary and not salary[0]:
                    salary = []
                print(f'----------\n{salary}')
                salary_dict = await self.finder.compose_salary_dict_from_salary_list(salary_list=salary)
                if salary_dict:
                    self.db.update_table_multi(
                        table_name=admin_database,
                        param=f"WHERE id={id}",
                        values_dict=salary_dict
                    )
                    pass
                else:
                    print("salary not found")
        else:
            print("You have not any vacancies")

    async def create_table(self, table_name):
        query = ''

        for table in valid_professions:
            query_part = f'SELECT {admin_table_fields} FROM {table}'
            query += f'{query_part} UNION '
        full_query = f'CREATE TABLE {table_name} AS {query[:-7]} ORDER BY created_at, id;'

        try:
            self.db.run_free_request('DROP TABLE IF EXISTS vacancies;')
            self.db.run_free_request(full_query)
            print (f'TABLE {table_name} READY')
        except Exception as e:
            print(e)

    def update_id(self, table_name):
        try:
            self.db.run_free_request('DROP SEQUENCE IF EXISTS new_id;')
            self.db.run_free_request('CREATE SEQUENCE new_id START 50000;')
            self.db.run_free_request(f"UPDATE {table_name} SET id = nextval('new_id');")
        except Exception as e:
            print(e)


