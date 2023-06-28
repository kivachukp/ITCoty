
fields = {
    'parsing': ['link_current_vacancy', 'title', 'body', 'check_link', 'found_id_by_link', 'found_title',
                     'found_body', 'found_id', 'found_vacancy_link', 'has_been_added_to_db', 'error', 'not_contacts',
                     'not_vacancy', 'profession', 'ma', 'mex'],
    'shorts': ['in_admin_channel', 'in_id_admin', 'in_title', 'in_body',
               'out_admin_channel', 'out_id_admin', 'out_title', 'out_body'],
    'digest': ['channel', 'message_id', 'link_current_vacancy', 'status', 'site'],
}

report_file_path = {
    'parsing': './report/excel/parsing_report.xlsx',
    'shorts': './report/excel/shorts_report.xlsx',
    'digest': './report/excel/digest_report.xlsx'
}