import asyncio
from aiogram.types import InlineKeyboardButton
from _apps.amin_panel_tg_view.views.bot.show_details._data_pattern import pattern

class AdditionalKeyboard():

    def __init__(self):
        self.all_professions = list(pattern.keys())
        self.professions_button = []
        self.sub_button = []
        self.subs = []
        self.markup = None

    async def show_professions_subs(self, vacancy_profession, vacancy_subs, markup):
        self.professions_button = []
        self.sub_button = []
        self.subs = []
        self.markup = markup
        pass

        for key in self.all_professions:
            self.professions_button.append(InlineKeyboardButton(f"✅{key}" if key in vacancy_profession else key, callback_data=f'profession:{key}'))

        for profession in vacancy_profession:
            # print(profession)
            try:
                # print(f"9999999999 pattern[profession] {pattern[profession]['sub']} 9999999999")
                subs = list(pattern[profession]['sub'].keys())
                for key in subs:
                    self.sub_button.append(InlineKeyboardButton(f"☑️{profession[:1]}/{key}" if key in vacancy_subs else f"{profession[:1]}/{key}",
                                                                callback_data=f'sub:{key}'))
                # self.subs.extend(list(pattern[profession]['sub'].keys()))
            except Exception as ex:
                # print(f'resolved error (2): {profession}', ex)
                pass

        # for key in self.subs:
        #     self.sub_button.append(InlineKeyboardButton(f"✅/{key}" if key in vacancy_subs else f"/{key}", callback_data=f'sub:{key}'))

        await self.compose_additional_rows_keyboard(step=5, button_list=self.professions_button)
        await self.compose_additional_rows_keyboard(step=4, button_list=self.sub_button)

        return self.markup

    async def compose_additional_rows_keyboard(self, step, button_list):
        for i in range(0, len(button_list), step):
            buttons_list = []
            for j in range(0, step):
                try:
                    buttons_list.append(button_list[i+j])
                except:
                    break
            self.markup.row(*buttons_list)

    async def check_profession(self, callback_data, card):
        press_profession = callback_data.split(':')[1]
        card_profession = card['profession'].split(', ')
        if press_profession in card_profession:

            # remove profession
            card_profession.remove(press_profession)
            card['profession'] = ', '.join(card_profession) if card_profession else ''

            # remove subs for this profession
            # if press_profession not in ['junior']:
            subs_raw_list = card['sub'].split("; ")
            # print('!!sub_list_raw:', subs_raw_list)
            subs_raw_list_copy = subs_raw_list.copy()
            for item in subs_raw_list_copy:
                if f"{press_profession}:" in item:
                    # print('item 69:', item)
                    subs_raw_list.remove(item)
            # print(f'11111111111 subs_raw_list {subs_raw_list} 11111111111111')
            card['sub'] = "; ".join(subs_raw_list) if subs_raw_list else None

        else:

            card['profession'] += ", " if card['profession'] else ''
            card['profession'] += press_profession
            card['sub'] = await self.define_sub(card['sub'])
            card['sub'] = f"{press_profession}: " if not card['sub'] else card['sub'] + f"; {press_profession}: "
        return card

    async def check_sub(self, callback_data, card):

        subs_raw_list = card['sub'].split("; ") if card['sub'] else []
        # print(f'3333333333 subs_raw_list {subs_raw_list} 3333333333')
        card_sub = []
        for i in subs_raw_list:
            if i:
                sub = i.split(": ")[1]
                if sub.strip():
                    card_sub.append(sub.strip())

        sub = callback_data.split(":")[1]
        if sub not in card_sub:
            for profession in card['profession'].split(', '):
                try:
                    if sub in pattern[profession]['sub']:
                        subs_raw_list.append(f"{profession}: {sub}")
                except Exception as ex:
                    # print('error details 1', ex)
                    pass
        else:
            for item in subs_raw_list:
                if sub in item:
                    subs_raw_list.remove(item)


        # print('ATTENTION! YOU MUST CHECK HOW DECOMPOSE SUBS IN SHORTS CODE IN COMPOSE_MESSAGE FUNCTION! THIS POINT FOR CHANGE COMPOSING SUBS IN MANUAL ADMIN PANEL!')
        card['sub'] = "; ".join(subs_raw_list) if subs_raw_list else ''
        return card

    async def define_sub(self, sub):
        return sub

if __name__ == '__main__':
    bd = AdditionalKeyboard()
    asyncio.run(bd.show_professions_subs(['backend'], []))

