from bot.helper.listeners.mega_listener import add_mega_download as add_mega_dl


async def add_mega_download(listener, path):
    await add_mega_dl(listener, path)
