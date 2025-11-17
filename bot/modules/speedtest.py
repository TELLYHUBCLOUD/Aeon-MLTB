from speedtest import Speedtest

from bot import LOGGER
from bot.core.aeon_client import TgClient
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import get_readable_file_size
from bot.helper.telegram_helper.message_utils import (
    delete_message,
    edit_message,
    send_message,
)


@new_task
async def speedtest(_, message):
    speed = await send_message(message, "⚡ Initializing Speedtest...")

    def get_speedtest_results():
        test = Speedtest()
        test.get_best_server()
        test.download()
        test.upload()
        return test.results

    result = await TgClient.bot.loop.run_in_executor(None, get_speedtest_results)
    if not result:
        await edit_message(speed, "❌ Speedtest failed to complete.")
        return
    string_speed = f"""
<blockquote>🚀 <b>SPEEDTEST INFO</b></blockquote>

<blockquote>📡 <b>Ping:</b> <code>{result.ping} ms</code>
📤 <b>Upload:</b> <code>{get_readable_file_size(result.upload / 8)}/s</code>
📥 <b>Download:</b> <code>{get_readable_file_size(result.download / 8)}/s</code>
🌐 <b>IP Address:</b> <code>{result.client["ip"]}</code></blockquote>
"""
    try:
        await send_message(message, string_speed, photo=result.share())
        await delete_message(speed)
    except Exception as e:
        LOGGER.error(str(e))
        await edit_message(speed, string_speed)
