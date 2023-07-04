import pandas as pd
from db_operations.scraping_db import DataBaseOperations
from report import report_variables

class Reports:
    report_file_path = report_variables.report_file_path

    def __init__(self, **kwargs):
        self.show_in_console = kwargs['show_in_console'] if 'show_in_console' in kwargs else None
        self.db = DataBaseOperations()
        self.switch_to_next = False
        self.excel_row = {}
        self.excel_sheet = {}
        self.keys_fields = []
        self.fields_values_dict = {}
        self.keys = report_variables

    def parsing_report(self, **kwargs):
        report_type = kwargs['report_type'] if 'report_type' in kwargs else 'parsing'

        if report_type not in self.excel_row:
            self.excel_row[report_type] = {}

        if kwargs:
            for key in kwargs:
                if key in self.keys.fields[report_type] and key != 'report_type':
                    self.excel_row[report_type][key] = kwargs[key]

    def parsing_switch_next(self, switch=None, report_type=None):
        if not report_type:
            report_type = 'parsing'

        if report_type not in self.keys.fields:
            return print('Incorrect report_type')

        if switch:
            if report_type not in self.excel_sheet:
                self.excel_sheet[report_type] = {}
            for i in self.keys.fields[report_type]:
                if i not in self.excel_row[report_type]:
                    if i in ['has_been_added_to_db', 'not_contacts', 'not_vacancy']:
                        self.excel_row[report_type][i] = False
                    else:
                        self.excel_row[report_type][i] = '-'
            for key in self.excel_row[report_type]:
                if key not in self.excel_sheet[report_type]:
                    self.excel_sheet[report_type][key] = []
                self.excel_sheet[report_type][key].append(self.excel_row[report_type][key])
            if self.show_in_console:
                self.print_data(report_type)
            self.excel_row = {}

    def print_data(self, report_type):
        print('*'*10)
        for key in self.excel_row[report_type]:
            value = self.excel_row[report_type][key][:30].replace('\n', ' ') \
                if type(self.excel_row[report_type][key]) is str \
                else self.excel_row[report_type][key]
            print(f"{key}: {value}")
        print('*'*10)
        pass

    async def add_to_excel(self, report_type=None):
        if not report_type:
            report_type = 'parsing'

        if report_type not in self.keys.fields:
            return print('Incorrect report_type')

        self.excel_row = {}
        try:
            df = pd.DataFrame(self.excel_sheet[report_type])
            df.to_excel(self.keys.report_file_path[report_type], sheet_name='Sheet1')
            print('got it')
            self.excel_sheet = {}
            return True
        except Exception as e:
            print(f"Something is wrong: {str(e)}")
            return False
