"""
There are all functions for the database updating by new updates anywhere
"""
from db_operations.scraping_db import DataBaseOperations
from utils.additional_variables.additional_variables import admin_database, valid_professions, archive_database
from helper_functions.parser_find_add_parameters.parser_find_add_parameters import FinderAddParameters

class DatabaseUpdateData:

    def __init__(self):
        self.db = DataBaseOperations()
        self.finder = FinderAddParameters()

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

