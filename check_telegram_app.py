import asyncio
import configparser

from telethon import TelegramClient

import settings.os_getenv as settings

config = configparser.ConfigParser()
config.read("./settings/config.ini")

api_id = settings.api_id
api_hash = settings.api_hash
username = settings.username

api_id_double = settings.api_id_double
api_hash_double = settings.api_hash_double
username_double = settings.username_double

async def connections():
    client = TelegramClient(username, int(api_id), api_hash)
    await client.start()
    if client.is_connected():
        print("Client is connected")
        await client.disconnect()
    else:
        print("Client NOT is connected")
    pass

    client = TelegramClient(username_double, int(api_id_double), api_hash_double)
    await client.start()
    if client.is_connected():
        print("Client is connected")
        await client.disconnect()
    else:
        print("Client NOT is connected")
    pass

asyncio.run(connections())
