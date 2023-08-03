import asyncio

from telethon.sync import TelegramClient

class ClientTelethon:
    def __init__(self):
        self.client = None

    def init(self):
        api_id = 13105861
        api_hash = '6b31f72207b8e47b588701a9761da84b'
        username = 'shorts'
        self.client = TelegramClient(username, api_id, api_hash)
        # self.client.start()
        return self.client

    def close_client(self):
        if self.client.is_connected:
            self.client.disconnect()


if __name__ == '__main__':
    ct = ClientTelethon()
    client = ct.init()
    pass