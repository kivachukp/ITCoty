import requests

class GetData:

    def __init__(self):
        pass

    def get_juniors(self):
        vacancies = requests.get('https://4dev.itcoty.ru/get-all-vacancies')
        vacancies = vacancies.json()['vacancies']

        vacancies_list = []
        for index in vacancies:
            vacancies_list.append(
                {
                    'id': vacancies[index]['id'],
                    'text': f"{vacancies[index]['vacancy']}\n\n{vacancies[index]['body']}",
                    'profession': vacancies[index]['profession'],
                    'sub': vacancies[index]['sub'],
                    'picture_url': '',
                    'video_url': '',
                    'sticker': ''
                }
            )

        return vacancies_list

    async def get_admin(self, profession=None, approve=None, local=False):
        approve = 'false' if not approve else approve
        profession = 'junior' if not profession else profession
        endpoint = f"http://127.0.0.1:5000/admin?prof={profession}&approve={approve}" if local else f"https://4dev.itcoty.ru/admin?prof={profession}&approve={approve}"
        # endpoint = f"https://4dev.itcoty.ru/admin?prof={profession}&approve={approve}"
        vacancies = requests.get(endpoint)
        vacancies_list = []

        if vacancies.status_code == 200 and 'error' not in vacancies.json():
            vacancies = vacancies.json()['vacancies']

            for vacancy in vacancies:

                vacancy = await self.refactor_professions_throw_subs(card=vacancy, local=local)

                text = ''
                for field in ['full_tags', 'full_anti_tags', 'vacancy', 'body']:
                    text += f"{vacancy[field]}\n" if vacancy[field] else ""

                vacancies_list.append(
                    {
                        'id': vacancy['id'],
                        'text': text,
                        'profession': vacancy['profession'],
                        'sub': vacancy['sub'],
                        'picture_url': '',
                        'video_url': '',
                        'sticker': ''
                    }
                )
        return vacancies_list


    async def approve(self, card, local=False):
        for i in ['picture_url', 'video_url', 'sticker', 'text']:
            if i in card:
                card.pop(i)

        card['approved'] = 'approves by admin'

        endpoint = "http://127.0.0.1:5000/admin-approve" if local else  "https://4dev.itcoty.ru/admin-approve"
        # endpoint = "https://4dev.itcoty.ru/admin-approve"
        response = requests.post(endpoint, json=card)
        return response

    async def delete(self, card, local=False):
        for i in ['picture_url', 'video_url', 'sticker', 'text']:
            if i in card:
                card.pop(i)

        card['approved'] = 'rejects by admin'
        endpoint = f"http://127.0.0.1:5000/admin-delete/{card['id']}" if local else f"https://4dev.itcoty.ru/admin-delete/{card['id']}"
        # endpoint = f"https://4dev.itcoty.ru/admin-delete/{card['id']}"
        response = requests.delete(endpoint)
        return response

    async def push(self, profession, token, chat_id, local=False):
        endpoint = f"http://127.0.0.1:5000/admin-push?prof={profession}&token={token}&chat_id={chat_id}" if local else f"https://4dev.itcoty.ru/admin-push?prof={profession}&token={token}&chat_id={chat_id}"
        # endpoint = f"https://4dev.itcoty.ru/admin-push?prof={profession}"
        response = requests.get(endpoint)
        return response

    async def put(self, data_dict, local=False):
        print(data_dict)
        endpoint = f"http://127.0.0.1:5000/admin-change" if local else f"https://4dev.itcoty.ru/admin-change"
        response = requests.put(endpoint, json=data_dict)
        return response.status_code

    async def refactor_professions_throw_subs(self, card, local):
        card['profession'] = ", ".join(list(set(card['profession'].split(", "))))

        if card['sub']:
            sub_list = card['sub'].split("; ")
            sub_dict = {}
            for item in sub_list:
                element_list = item.split(": ")
                if element_list[0] not in ['junior']:
                    sub_dict[element_list[0]] = element_list[1]
            sub_keys = set(sub_dict.keys())
            profession_set_old = set(card['profession'].split(", "))
            profession_set_new = profession_set_old.union(sub_keys)
            card['profession'] = ", ".join(list(filter(None, profession_set_new)))

            if profession_set_new != profession_set_old:
                print(await self.put(data_dict={'profession': ", ".join(profession_set_new), 'id': card['id']}, local=local))
                pass
        else:
            for item in set(card['profession'].split(", ")):
                if not card['sub']:
                    card['sub'] = f"{item}: "
                else:
                    card['sub'] += f"; {item}: "

        return card


if __name__ == '__main__':
    get_data = GetData()
    vacancies = get_data.get_juniors()