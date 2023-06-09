from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State



class TelegramApp:

    def __init__(self, kwargs):
        self.client = kwargs['client'] if 'client' in kwargs else None
        self.bot_aiogram = kwargs['bot_aiogram'] if 'bot_aiogram' in kwargs else None
        self.chat_id = kwargs['chat_id'] if 'chat_id' in kwargs else None
        # self.api = kwargs['api'] if 'api' in kwargs else None
        # self.api_hash = kwargs['api_hash'] if 'api_hash' in kwargs else None
        # self.username = kwargs['username'] if 'username' in kwargs else None
        self.number = None
        self.two_f_code = None
        self.message_handler = self.bot_aiogram.dp.message_handler

    class Form_get_number_and_2Fcode(StatesGroup):
            number = State()
            two_f_code = State()

    @self.message_handler(state=Form_get_number_and_2Fcode.number)
    async def show_db_records_form(self, message: types.Message, state: FSMContext):
        async with state.proxy():
            self.number = message.text

    @self.message_handler(state=Form_get_number_and_2Fcode.two_f_code)
    async def show_db_records_form(self, message: types.Message, state: FSMContext):
        async with state.proxy():
            self.two_f_code = message.text
        await state.finish()



    async def start_app(self):
        await self.client.connect()
        print('The attempt to connection')
        if not self.client.is_user_authorized():
            # собрать телефон и код защиты
            await self.bot_aiogram.send_message(self.chat_id, 'Input the phone number')
            await Form_get_number_and_2Fcode().number.set()



    async def print_message(self, text):
        if self.bot_aiogram and self.chat_id:
            await self.bot_aiogram.send_message(self.chat_id, text)
        else:
            print(text)
