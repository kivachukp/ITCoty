import re

from patterns._export_pattern import export_pattern
from utils.additional_variables import additional_variables as variables

class VacancyFilter:

    def __init__(self, **kwargs):
        self.report = kwargs['report'] if 'report' in kwargs else None

        self.capitalize = variables.not_lower_professions

        self.result_dict2 = {'vacancy': 0, 'contacts': 0, 'fullstack': 0, 'frontend': 0, 'backend': 0, 'pm': 0,
                             'mobile': 0, 'game': 0, 'designer': 0, 'hr': 0, 'analyst': 0, 'qa': 0, 'ba': 0,
                             'product': 0, 'devops': 0, 'marketing': 0, 'sales_manager': 0, 'junior': 0, 'middle': 0,
                             'senior': 0}

        self.valid_profession_list = variables.valid_professions
        self.export_pattern = export_pattern
        self.not_lower_professions = variables.not_lower_professions
        self.excel_dict = {}
        self.profession = {}

    def sort_profession(
            self,
            title,
            body=None,
            # check_contacts=True,
            # check_profession=True,
            # check_vacancy=True,
            # check_vacancy_only_mex=False,
            # get_params=True,
            # check_level=True,
            # only_one_profession_sub=True,
            **kwargs
    ):
        check_contacts = True if 'check_contacts' not in kwargs else kwargs['check_contacts']
        check_profession = True if 'check_profession' not in kwargs else kwargs['check_profession']
        check_vacancy = True if 'check_vacancy' not in kwargs else kwargs['check_vacancy']
        check_vacancy_only_mex = False if 'check_vacancy_only_mex' not in kwargs else kwargs['check_vacancy_only_mex']
        get_params = True if 'get_params' not in kwargs else kwargs['get_params']
        check_level = True if 'check_level' not in kwargs else kwargs['check_level']
        only_one_profession_sub = True if 'only_one_profession_sub' not in kwargs else kwargs['only_one_profession_sub']
        low = False if 'low' not in kwargs else kwargs['low']

        self.profession['tag'] = ''
        self.profession['anti_tag'] = ''
        self.profession['profession'] = []
        self.profession['sub'] = []
        self.profession['level'] = ''

        params = {}
        vacancy = f"{title}\n{body}"

        if check_profession:
            # if it is not vacancy, return no_sort
            if check_vacancy:
                result = self.check_parameter(
                    pattern=self.export_pattern['data']['vacancy'],
                    vacancy=vacancy,
                    key='vacancy',
                    check_only_mex=check_vacancy_only_mex,
                    low=low
                )

                self.result_dict2['vacancy'] = result['result']
                self.profession['tag'] += result['tags']
                self.profession['anti_tag'] += result['anti_tags']

                if not self.result_dict2['vacancy']:
                    if self.report:
                        self.report.parsing_report(not_vacancy=True, report_type='parsing')
                    # self.profession['profession'] = {'no_sort'}
                    # print(f"line84 {self.profession['profession']}")
                    print("= vacancy not found =")
                    return {'profession': self.profession, 'params': {}}

            if check_contacts:
                # if it is without contact, return no_sort
                result = self.check_parameter(
                    pattern=self.export_pattern['data']['contacts'],
                    vacancy=vacancy,
                    key='contacts',
                    low=low
                )
                self.result_dict2['contacts'] = result['result']
                self.profession['tag'] += result['tags']
                self.profession['anti_tag'] += result['anti_tags']

                if not self.result_dict2['contacts']:
                    self.profession['profession'] = {'no_sort'}
                    if self.report:
                        self.report.parsing_report(not_contacts=True, report_type='parsing')
                    # print(f"not contacts {self.profession['profession']}")
                    print("= contacts not found =")
                    return {'profession': self.profession, 'params': {}}

            # ---------------- professions -----------------
            vacancy_name = self.get_vacancy_name(
                text=vacancy
            ).capitalize()

            if vacancy_name and (vacancy_name == title or '#' in title):
                search_profession_text = vacancy_name
            else:
                search_profession_text = title
            pass
            for item in self.valid_profession_list:
                result = self.search_profession(vacancy=search_profession_text, item=item, mex=True)
                if result['result']:
                    self.profession['profession'].append(result['result'])
                    self.profession['tag'] += result['tags']
                    self.profession['anti_tag'] += result['anti_tags']

            if not self.profession['profession']:
                for item in self.valid_profession_list:
                    result = self.search_profession(vacancy=vacancy, item=item)
                    if result['result']:
                        self.profession['profession'].append(result['result'])
                        self.profession['tag'] += result['tags']
                        self.profession['anti_tag'] += result['anti_tags']

            if 'fullstack' in self.profession['profession']:
                self.transform_fullstack_to_back_and_front(text=vacancy)

            if not self.profession['profession']:
                self.profession['profession'] = {'no_sort'}

            self.profession['profession'] = set(self.profession['profession'])

            # -------------- get subprofessions -------------------------
            if 'no_sort' not in self.profession['profession']:
                self.get_sub_profession(text=vacancy)
            else:
                self.profession['sub'] = []

            if self.profession['sub']:
                self.compose_junior_sub(key_word='junior')
        # --------------------- end -------------------------
        if get_params:
            params = self.get_params(text=vacancy)

        if check_level:
            level_list = []

            for item in self.export_pattern['level']:
                result = self.search_profession(
                    vacancy=vacancy,
                    item=item,
                    mex=True,
                    pattern_key='level'
                )
                pass
                if result['result']:
                    level_list.append(result['result'])
            if level_list:
                self.profession['level'] = ", ".join(level_list)
            else:
                self.profession['level'] = ''

        if only_one_profession_sub and check_profession:
            self.reduce_profession()

        return {'profession': self.profession, 'params': params}

    def get_sub_profession(self, text):
        self.profession['sub'] = {}

        for prof in self.profession['profession']:
            prof = prof.strip()

            union_sub = {}
            if prof in self.valid_profession_list:
                self.profession['sub'][prof] = []
                current_profession_sub_list = self.export_pattern['professions'][prof]['sub']
                for sub in current_profession_sub_list:
                    pattern = self.export_pattern['professions'][prof]['sub'][sub]

                    result = self.check_parameter(
                        pattern=pattern,
                        vacancy=text,
                        key=sub,
                        low=False
                    )
                    if result['result']:
                        self.profession['sub'][prof].append(result['result'])

    def check_parameter(self, pattern, vacancy, key, low=False, mex=True, only_one_profession_sub=False, check_only_mex=False):
        result = 0
        tags = ''
        anti_tags = ''

        if low:
            vacancy = vacancy.lower()
        if not check_only_mex:
            for word in pattern['ma']:
                if low:
                    word = word.lower()
                match = []
                try:
                    match = set(re.findall(rf"{word}", vacancy))
                except Exception as e:
                    with open('./excel/filter_jan_errors.txt', 'a+', encoding='utf-8') as f:
                        f.write(f"word = {word}\nvacancy = {vacancy}\nerror = {e}\n------------\n\n")

                if match:
                    result += len(match)
                    tags += f'MA {key}={match}\n'
        else:
            result = 1

        if result and mex:
            for anti_word in pattern['mex']:
                if low:
                    anti_word = anti_word.lower()
                match = []
                try:
                    match = set(re.findall(rf"{anti_word}", vacancy))
                except Exception as e:
                    with open('./excel/filter_jan_errors.txt', 'a+', encoding='utf-8') as f:
                        f.write(f"word = {anti_word}\nvacancy = {vacancy}\nerror = {e}\n------------\n\n")

                if match:
                    result = 0
                    anti_tags += f'MEX {key}={match}\n'
                    break
        else:
            anti_tags = ''
        pass
        return {'result': key if result else '', 'tags': tags, 'anti_tags': anti_tags}

    def get_params(self, text, all_fields_null=False):
        params = {}
        params['company'] = self.get_company_new(text)
        params['job_type'] = self.get_remote_new(text)
        params['relocation'] = self.get_relocation_new(text)
        params['english'] = self.english_requirements_new(text)
        params['vacancy'] = self.get_vacancy_name(text, self.profession['sub'])
        return params

    def transform_fullstack_to_back_and_front(self, text):

        for anti_word in self.export_pattern['professions']['backend']['mex']:
            match = re.findall(rf"{anti_word.lower()}", text.lower())
            if match:
                self.profession['anti_tag'] += f'TAG ANTI backend={match}\n'
            else:
                self.profession['profession'].add('backend')

        for anti_word in self.export_pattern['professions']['frontend']['mex']:
            match = re.findall(rf"{anti_word.lower()}", text.lower())
            if match:
                self.profession['anti_tag'] += f'TAG ANTI frontend={match}\n'
            else:
                self.profession['profession'].add('frontend')

        self.profession['profession'].discard('fullstack')

    def get_company_new(self, text):
        pass

    def english_requirements_new(self, text):
        english_pattern = "|".join(self.export_pattern['others']['english']['ma'])
        match = re.findall(english_pattern, text)
        if match:
            match = match[0].replace('\n', '').replace('"', '').replace('#', '').replace('.', '')
            match = match.strip()
            if match[-1:] == '(':
                match = match[:-1]
        else:
            match = ''
        return match

    def get_relocation_new(self, text):
        relocate_pattern = "|".join(self.export_pattern['others']['relocate']['ma'])
        match = re.findall(rf"{relocate_pattern}", text)
        if match:
            return match[0]
        else:
            return ''

    def get_remote_new(self, text):
        remote_pattern = "|".join(self.export_pattern['others']['remote']['ma'])
        match = re.findall(rf"{remote_pattern}", text)
        if match:
            return match[0]
        else:
            return ''

    def clean_company_new(self, company):
        pattern = "^[Cc]ompany[:]{0,1}|^[Кк]омпания[:]{0,1}" #clear company word
        pattern_russian = "[а-яА-Я\s]{3,}"
        pattern_english = "[a-zA-Z\s]{3,}"

        # -------------- if russian and english, that delete russian and rest english -----------
        if re.findall(pattern_russian, company) and re.findall(pattern_english, company):
            match = re.findall(pattern_english, company)
            company = match[0]

        # -------------- if "company" in english text, replace this word
        match = re.findall(pattern, company)
        if match:
            company = company.replace(match[0], '')

        return company.strip()

    def get_vacancy_name(self, text, sub=None):
        vacancy = ''
        match = []

        if not vacancy:
            for pro in variables.valid_professions:
                if pro == 'no_sort':
                    pass
                    # pattern = self.export_pattern['others']['vacancy']['sub']['backend_vacancy']
                # else:
                pattern = self.export_pattern['others']['vacancy']['sub'][f'{pro}_vacancy']
                if pattern:
                    match = re.findall(rf"{pattern}", text)
                    try:
                        match_str = ''.join(match)
                        if len(''.join(match)) > 0:
                            vacancy = match[0]
                            break
                    except Exception as e:
                        print('Error: ', e)

        if not vacancy:
            vacancy_pattern = self.export_pattern['others']['vacancy']['sub']['common_vacancy']
            if vacancy_pattern:
                match = re.findall(rf"{vacancy_pattern}", text)
                try:
                    match_str = ''.join(match)
                    if len(''.join(match)) > 0:
                        vacancy = match[0]
                except Exception as e:
                    print('Error: ', e)

        if sub and not vacancy:
            for key in sub:
                if sub[key]:
                    vacancy = f"{', '.join(sub[key])} {key}"
                    break
        if vacancy:
            vacancy = self.clean_vacancy_from_get_vacancy_name(vacancy)
        return vacancy

    def clean_vacancy_from_get_vacancy_name(self, vacancy):
        vacancy = re.findall(r"[a-zA-Zа-яА-Я0-9:;-_\\/\s]+", vacancy)[0]
        vacancy = re.sub(rf"{variables.clear_vacancy_trash_pattern}", "", vacancy)
        return vacancy.strip()

    def compose_junior_sub(self, key_word):
        if key_word in self.profession['sub'].keys():
            for key in self.profession['sub'].keys():
                if key != key_word:
                    self.profession['sub'][key_word].append(key)
        return self.profession

    def search_profession(self, vacancy, item, mex=True, pattern_key=None):
            if item in self.not_lower_professions:
                low = False
            else:
                low = True

            if item == 'product':
                item = 'pm'

            if not pattern_key:
                pattern_key = 'professions'

            result = self.check_parameter(
                pattern=self.export_pattern[pattern_key][item],
                vacancy=vacancy,
                low=low,
                key=item,
                mex=mex,
            )
            return result

    def reduce_profession(self):
        junior = False
        new_sub = {}
        prof_list = []
        subs = []

        prof_list.extend(self.profession['profession'])
        if 'junior' in prof_list:
            junior = True
            prof_list.remove('junior')
        if prof_list:
            self.profession['profession'] = set()
            self.profession['profession'].add(prof_list[0])
        if junior:
            self.profession['profession'].add('junior')

        subs.extend(self.profession['sub'])
        for sub in subs:
            if sub in self.profession['profession']:
                new_sub[sub] = self.profession['sub'][sub][0] if self.profession['sub'][sub] else []
        self.profession['sub'] = new_sub
