# import asyncio
#
# from aiogram import Bot, Dispatcher, types
# from aiogram.contrib.fsm_storage.memory import MemoryStorage
# from aiogram.utils import executor
#
# storage = MemoryStorage()
# bot = Bot(token='5730794427:AAH_XjUoNFS5RB2Wzav61brF2u4BHtNFURM')
# dp = Dispatcher(bot, storage=storage)
#
# def main():
#
#     @dp.message_handler(commands=['start'])
#     async def send_welcome(message: types.Message):
#         text = "Дайджест для #Junior за 26.06.2023\nВакансии для '<a href=https://telegra.ph/Dajdzhest-vakansij-dlya-Game-za-26062023-06-26-17><b>Game</b></a>"
#         text = f"Дайджест для #Junior за 26.06.2023\n\nВакансии для <a href=\"https://telegra.ph/Dajdzhest-vakansij-dlya-Game-za-26062023-06-26-17\"><b>#Game</b>\n</a>"
#         text = 'Вакансии для <a href="https://telegra.ph/Dajdzhest-vakansij-dlya-Game-za-26062023-06-26-19"><b>#Game</b></a>'
#         await bot.send_message(message.chat.id, text, parse_mode='html')
#         await bot.send_photo(message.chat.id, photo='https://telegra.ph/file/8c105a3929d755d5a6ffb.jpg', caption=text, parse_mode='html')
#
#     executor.start_polling(dp, skip_updates=True)
#
#
# if __name__ == '__main__':
#     main()

# from patterns._export_pattern import export_pattern
#
# professions_and_subs = {}
# for key in export_pattern['professions']:
#     if key not in ['ba', 'junior', 'fullstack']:
#         professions_and_subs[key] = list(export_pattern['professions'][key]['sub'].keys())
# for key in professions_and_subs:
#     with open ('D:/Python/ITCoty/utils/custom_subs/custom_subs.py', 'a') as file:
#         file.write(f"'{key}': [")
#     print('kty: ' , key)
#     for name in professions_and_subs[key]:
#         print(name)
#         with open('D:/Python/ITCoty/utils/custom_subs/custom_subs.py', 'a') as file:
#             file.write(f"'{name}', ")
#     with open('D:/Python/ITCoty/utils/custom_subs/custom_subs.py', 'a') as file:
#         file.write(f"]\n")
#
# pass

from datetime import datetime, timedelta

today = datetime.now()
tommorow = datetime(2023, 6, 30, 10, 30, 0, 0)

a = tommorow - today
seconds = a.seconds
print(seconds)

import re

with open('./test.txt', 'r', encoding='utf=8') as file:
    text = file.read()
    text = re.sub(r'\n{2,}', '\n\n', text)
print(text)

