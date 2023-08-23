from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from _apps.amin_panel_tg_view.views.bot.show_details.show_details import AdditionalKeyboard

class BotHelper:

    def __init__(self, bot):
        self.bot = bot
        self.back = InlineKeyboardButton('<<< back', callback_data='back')
        self.forward = InlineKeyboardButton('forward >>>', callback_data='forward')
        self.empty = InlineKeyboardButton(' ', callback_data=' ')
        self.addkeyboard = AdditionalKeyboard()
        self.card = None

    async def compose_inline_markup(self, menu_current_point, menu_history, menu_offset, row=1):
        markup = InlineKeyboardMarkup()
        buttons_list = menu_current_point.keys()

        if menu_history:
            if len(menu_history) > 1:
                if menu_offset < len(menu_history) - 1:
                    markup.row(self.empty, self.forward)
                elif menu_offset == len(menu_history) - 1:
                    markup.row(self.back, self.empty)
                else:
                    markup.row(self.back, self.forward)


        callback_dict = {}
        for element in buttons_list:
            if type(menu_current_point[element]) is dict:
                button = InlineKeyboardButton(element, callback_data=menu_current_point[element]['callback'])
                markup.add(button)
                callback_dict[menu_current_point[element]['callback']] = element
        return {'markup': markup, 'callback_dict': callback_dict}

    async def process_callback(self, menu_current_point):
        if 'output' in menu_current_point:
            self.cards_dict = {}
            for index in range(0, len(menu_current_point['output'])):
                self.cards_dict[index] = menu_current_point['output'][index]
            return self.cards_dict
        else:
            return None


    async def show_cards(self, cards, offset=0):
        markup = None
        previous = {'<<<': 'previous'}
        next = {'>>>': 'next'}
        empty = {' ': ' '}
        card_number = {f"{offset+1}/{len(cards)}": " "}
        approve = {'APPROVE': 'approve'}
        delete = {'⛔️ DELETE': 'delete'}

        self.card = cards[offset]

        # print('**** profession_card: ', self.card['profession'])
        # print('**** sub_card: ', self.card['sub'])

        length = len(cards)
        if length > 0:
            if length > 1:
                if offset < length -1:
                    if offset == 0:
                        markup = await self.compose_card_keyboard(keyboard_dict = {'row1': {**empty, **card_number, **next},'row2': {**approve, **delete},})
                    elif offset > 0:
                        markup = await self.compose_card_keyboard(keyboard_dict={'row1': {**previous, **card_number, **next},'row2': {**approve, **delete}})
                elif offset == length -1:
                    markup = await self.compose_card_keyboard(keyboard_dict={'row1': {**previous, **card_number, **empty},'row2': {**approve, **delete}})
            else:
                markup = await self.compose_card_keyboard(keyboard_dict={'row2': {**approve, **delete}})
        else:
            pass

        if self.card['video_url']:
            text = f"{self.card['video_url']}\n{self.card['text']}"
        elif self.card['picture_url']:
            text = f"{self.card['picture_url']}\n{self.card['text']}"
        else:
            text = self.card['text']

        text = text[0:4096] if len(text)>4096 else text
        return {'text': text, 'markup': markup}

    async def compose_card_keyboard(self, keyboard_dict:dict):

        pass

        markup = InlineKeyboardMarkup()
        for row in keyboard_dict:
            buttons_list = []
            for key in keyboard_dict[row]:
                buttons_list.append(InlineKeyboardButton(text=key, callback_data=keyboard_dict[row][key]))
            markup.row(*buttons_list)

        # ----------- additional keyboard -------------
        subs_list = []
        profession_list = []
        try:
            profession_list = self.card['profession'].split(', ') if self.card['profession'] else []
        except Exception as ex:
            # print('error helper 1', ex)
            pass
        subs_temp = self.card['sub'].split('; ') if self.card['sub'] else []
        # print('sub_temps: ', subs_temp)

        for i in subs_temp:
            sub = ''
            # print(f'CURRENT i: {i}')
            if ':' not in i:
                print(f">>>>>>>>>>>>> i: {i} <<<<<<<<<<<<<<<")
            try:
                sub = i.strip().split(':')[1]
            except Exception as ex:
                print('Error helper 555:', ex)
            if sub:
                subs_list.append(sub.strip())
                pass

        markup = await self.addkeyboard.show_professions_subs(
            vacancy_profession=profession_list,
            vacancy_subs=subs_list,
            markup=markup
        )
        return markup
