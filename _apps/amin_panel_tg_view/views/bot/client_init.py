import asyncio

from telethon.sync import TelegramClient

class ClientTelethon:
    def __init__(self):
        self.client = None

    def init(self):
        api_id = 11944864
        api_hash = '7f98880741868033195cefeb436c2407'
        username = 'shorts_pusher'
        self.client = TelegramClient(username, api_id, api_hash)
        self.client.start()
        return self.client

if __name__ == '__main__':
    ct = ClientTelethon()
    client = ct.init()
    pass