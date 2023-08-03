import asyncio
import re


class ShowProgress:

    def __init__(self, bot_dict):
        self.percent = 0
        self.bot = bot_dict['bot']
        self.chat_id = bot_dict['chat_id']
        self.message = None

    async def reset_percent(self):
        self.percent = 0

    async def start(self):
        self.message = await self.bot.send_message(self.chat_id, f"progress | {self.percent}%")
        return self.message

    async def show_the_progress(self, message, current_number, end_number):
        self.message = message if message else self.message
        check = current_number * 100 // end_number
        if check > self.percent:
            quantity = check // 5
            self.percent = check
            while True:
                try:
                    self.message = await self.bot.edit_message_text(
                        f"progress {'|' * quantity} {self.percent}%", self.message.chat.id, self.message.message_id)
                    return self.message
                except Exception as ex:
                    if 'flood control' in ex.args[0]:
                        print("\n--------------\nFlood control\n--------------\n")
                        match = re.findall(r"[0-9]{1,4} seconds", ex.args[0])
                        if match:
                            seconds = match[0].split(' ')[0]
                            await asyncio.sleep(int(seconds) + 5)

