import asyncio
import configparser
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from _apps.amin_panel_tg_view.views.bot.bot_helper import BotHelper
from _apps.amin_panel_tg_view.views.bot.menu.menu_structure import get_inline_menu
from _apps.amin_panel_tg_view.views.bot.show_details.show_details import AdditionalKeyboard
from _apps.amin_panel_tg_view.data.get_data import GetData
# from views.bot.client_init import ClientTelethon

class BotView:
    def __init__(self, token):
        # self.client = ClientTelethon().init()
        self.bot = Bot(token=token)
        self.get_data = GetData()
        self.__token = token
        storage = MemoryStorage()
        self.dp = Dispatcher(self.bot, storage=storage)
        self.details = AdditionalKeyboard()
        self.user_data = {}
        self.helper = BotHelper(bot=self.bot)
        self.markup = None

        self.menu_current_point = {} # active inline buttons dict
        self.menu_history = []
        self.menu_offset = 0
        self.callback_data_dict = {}
        self.menu_title = []
        self.prof = ''
        self.card_offset = 0
        self.cards = None

        self.info_message = None
        self.message = None
        self.bar_message = None
        self.additional_menu_message = None

        self.bar_keyboard = None

        self.local = True


    def handlers(self):

        @self.dp.message_handler(commands=['start'])
        async def start(message: types.Message):
            await self.get_new_vacancies(message)

        @self.dp.message_handler(content_types=['text'])
        async def message_text(message):
            if message.text == 'PUSH':
                await self.bot.delete_message(message.chat.id, message.message_id)

                # if self.prof:
                #     await self.push(message=message, local=self.local)
                # else:
                #     await self.bot.delete_message(message.chat.id, message.message_id)
                #     self.info_message = await self.bot.send_message(message.chat.id, "You must choose the profession")

            elif message.text == 'GET NEW VACANCIES':
                if self.message:
                    await self.get_new_vacancies(message)

            else:
                await self.bot.delete_message(message.chat.id, message.message_id)

        @self.dp.callback_query_handler()
        async def catch_callback(callback: types.CallbackQuery):
            if callback.data in self.callback_data_dict.keys():
                if '**' in callback.data:
                    if self.info_message:
                        await self.info_message.delete()
                        self.info_message = None
                    self.prof = callback.data[2:]

                await self.callback_in_callback_data_dict(message=callback.message, callback_data=callback.data)

            if callback.data == 'back':
                self.menu_offset -= 1
                self.menu_current_point = self.menu_history[self.menu_offset]
                title = self.menu_title[self.menu_offset]
                await self.send_menu_message(callback.message, title)

            if callback.data == 'forward':
                self.menu_offset += 1
                self.menu_current_point = self.menu_history[self.menu_offset]
                title = self.menu_title[self.menu_offset]
                await self.send_menu_message(callback.message, title)

            if callback.data == 'next':
                await self.callback_is_next(message=callback.message)

            if callback.data == 'previous':
                await self.callback_is_previous(message=callback.message)

            if callback.data == 'show details':
                pass

            # --------- additional keyboard ---------------
            if 'profession:' in callback.data:
                self.cards[self.card_offset] = await self.details.check_profession(callback_data=callback.data, card=self.cards[self.card_offset])
                data = await self.helper.show_cards(cards=self.cards, offset=self.card_offset)
                await self.bot.edit_message_text(data['text'], callback.message.chat.id, self.message.message_id,
                                                 reply_markup=data['markup'])

            if 'sub:' in callback.data:
                self.cards[self.card_offset] = await self.details.check_sub(callback_data=callback.data,
                                                                                   card=self.cards[self.card_offset])
                data = await self.helper.show_cards(cards=self.cards, offset=self.card_offset)
                await self.bot.edit_message_text(data['text'], callback.message.chat.id, self.message.message_id,
                                                 reply_markup=data['markup'])

            if callback.data in ['approve', 'delete']:
                if callback.data == 'approve':
                    print("FINAL approved sub: ", self.cards[self.card_offset]['sub'])
                    print("FINAL approved profession: ", self.cards[self.card_offset]['profession'])
                    await self.get_data.approve(card=self.cards[self.card_offset], local=self.local)
                elif callback.data == 'delete':
                    await self.get_data.delete(card=self.cards[self.card_offset], local=self.local)

                self.cards = await self.update_cards()

                if self.cards:
                    data = await self.helper.show_cards(cards=self.cards, offset=self.card_offset)
                    await self.bot.edit_message_text(data['text'], callback.message.chat.id, self.message.message_id,
                                                     reply_markup=data['markup'])
                else:
                    await self.bar_message.delete()
                    self.bar_message = None
                    await self.message.delete()
                    self.message = await self.bot.send_message(
                        callback.message.chat.id,
                        "There are no more vacancies.\nbutton PUSH must be pressed ⬇️",
                        reply_markup=self.bar_keyboard
                    )

        executor.start_polling(self.dp, skip_updates=True)

    async def callback_in_callback_data_dict(self, message, callback_data):

        self.menu_title.append(self.callback_data_dict[callback_data])
        self.menu_current_point = self.menu_current_point[self.callback_data_dict[callback_data]]
        self.menu_history.append(self.menu_current_point)
        self.menu_offset += 1

        self.cards = await self.helper.process_callback(self.menu_current_point)
        if self.cards:
            data = await self.helper.show_cards(self.cards)
            await self.bot.edit_message_text(data['text'], message.chat.id, self.message.message_id, reply_markup=data['markup'])
        else:
            await self.send_menu_message(message=message, text=self.callback_data_dict[callback_data])

    async def callback_is_next(self, message):
        if self.card_offset == len(self.cards) - 1:
            self.card_offset = 0
        else:
            self.card_offset += 1
        data = await self.helper.show_cards(self.cards, self.card_offset)
        await self.bot.edit_message_text(data['text'], message.chat.id,self.message.message_id, reply_markup=data['markup'])

    async def callback_is_previous(self, message):
        if self.card_offset == 0:
            self.card_offset = len(self.cards) -1
        else:
            self.card_offset -= 1
        data = await self.helper.show_cards(self.cards, self.card_offset)
        await self.bot.edit_message_text(data['text'], message.chat.id,self.message.message_id, reply_markup=data['markup'])

    async def send_menu_message(self, message, text):
        response = await self.helper.compose_inline_markup(self.menu_current_point, self.menu_history, self.menu_offset)
        self.markup = response['markup']
        self.callback_data_dict = response['callback_dict']
        await self.bot.edit_message_text(text, message.chat.id, self.message.message_id, reply_markup=self.markup)

    async def update_cards(self):
        self.cards.pop(self.card_offset)
        cards = {}
        number = 0
        for key in self.cards:
            cards[number] = self.cards[key]
            number += 1
        if self.card_offset > len(cards) -1:
            self.card_offset = len(cards) -1
        return cards

    async def push(self, message, local):
        if self.bar_message:
            await self.bar_message.delete()
            self.bar_message = None
        if self.message:
            await self.message.delete()
            self.message = None

        await self.bot.delete_message(message.chat.id, message.message_id)
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.get_data.push(profession=self.prof, token=self.__token, chat_id=message.chat.id, local=local))
        # await self.get_data.push(profession=self.prof, token=self.__token, local=local)
        self.bar_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        bar_button = KeyboardButton(text="GET NEW VACANCIES")
        self.bar_keyboard.add(bar_button)
        self.message = await self.bot.send_message(message.chat.id, 'Done!\nNew vacancies by button below ⬇️', reply_markup=self.bar_keyboard)

    async def get_new_vacancies(self, message):
        self.markup = None

        self.menu_current_point = {}  # active inline buttons dict
        self.menu_history = []
        self.menu_offset = 0
        self.callback_data_dict = {}
        self.menu_title = []

        self.card_offset = 0
        self.cards = None

        self.prof = None

        if self.message:
            await self.message.delete()
            self.message = None
        if self.bar_message:
            await self.bar_message.delete()
            self.bar_message = None

        self.bar_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        bar_button = KeyboardButton(text="PUSH")
        self.bar_keyboard.add(bar_button)
        self.bar_message = await self.bot.send_message(message.chat.id,
                                                       "You can press PUSH in bot bar for get digest",
                                                       reply_markup=self.bar_keyboard)

        await self.bot.delete_message(message.chat.id, message.message_id)
        self.message = await self.bot.send_message(message.chat.id, 'wait...')

        title = "Make a choice"
        self.menu_current_point = await get_inline_menu(self.local)
        self.menu_history.append(self.menu_current_point)
        self.menu_title.append(title)
        await self.send_menu_message(message, title)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("./../../settings/config.ini")
    __token = config['Bot']['token']

    bot = BotView(token=__token)
    bot.handlers()