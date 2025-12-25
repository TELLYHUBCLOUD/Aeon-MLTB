from asyncio import create_subprocess_exec, sleep
from asyncio.subprocess import PIPE
from re import search as re_search

from bot import LOGGER, task_dict, task_dict_lock
from bot.core.config_manager import Config
from bot.helper.ext_utils.links_utils import get_mega_link_type
from bot.helper.mirror_leech_utils.status_utils.mega_status import MegaStatus


class MegaAppListener:
    def __init__(self, listener, path):
        self.listener = listener
        self.path = path
        self.proc = None
        self.name = ""
        self.size = 0
        self.processed_bytes = 0
        self.speed = 0
        self.is_cancelled = False

    async def _login(self):
        if Config.MEGA_EMAIL and Config.MEGA_PASSWORD:
            cmd = ["mega-login", Config.MEGA_EMAIL, Config.MEGA_PASSWORD]
            proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
            await proc.communicate()
            if proc.returncode != 0:
                LOGGER.warning("Mega login failed, proceeding without login")

    async def _logout(self):
        cmd = ["mega-logout"]
        proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        await proc.communicate()

    async def execute(self):
        await self._login()
        link_type = get_mega_link_type(self.listener.link)
        
        if link_type == "folder":
            cmd = ["mega-get", "-m", self.listener.link, self.path]
        else:
            cmd = ["mega-get", self.listener.link, self.path]

        self.proc = await create_subprocess_exec(*cmd, stdout=PIPE, stderr=PIPE)
        
        await self._process_output()
        await self._logout()

    async def _process_output(self):
        while True:
            if self.is_cancelled:
                self.proc.kill()
                break

            line = await self.proc.stdout.readline()
            if not line:
                break

            line = line.decode().strip()
            
            # Parse mega-get output for progress
            if match := re_search(r"(\d+)%", line):
                try:
                    progress = int(match.group(1))
                    if self.size > 0:
                        self.processed_bytes = (progress / 100) * self.size
                except Exception:
                    pass
            
            # Parse size if available
            if "bytes" in line.lower() and not self.size:
                if match := re_search(r"(\d+)\s*bytes", line):
                    try:
                        self.size = int(match.group(1))
                    except Exception:
                        pass

        await self.proc.wait()
        
        if self.proc.returncode != 0 and not self.is_cancelled:
            stderr = await self.proc.stderr.read()
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            await self.listener.on_download_error(f"Mega download failed: {error_msg}")
        elif not self.is_cancelled:
            await self.listener.on_download_complete()

    async def cancel_task(self):
        self.is_cancelled = True
        if self.proc:
            self.proc.kill()
        await self._logout()


async def add_mega_download(listener, path):
    mega_listener = MegaAppListener(listener, path)
    
    async with task_dict_lock:
        task_dict[listener.mid] = MegaStatus(
            listener,
            mega_listener,
            listener.mid,
        )

    await listener.on_download_start()
    await mega_listener.execute()
