from bot.helper.ext_utils.status_utils import MirrorStatus, get_readable_file_size

class LuluStatus:
    def __init__(self, listener, gid, status):
        self.listener = listener
        self._size = self.listener.size
        self._gid = gid
        self._status = status
        self.tool = "LuluStream"

    def gid(self):
        return self._gid

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self._size)

    def status(self):
        return MirrorStatus.STATUS_UPLOAD

    def processed_bytes(self):
        return 0

    def progress(self):
        return "0%"

    def speed(self):
        return "0B/s"

    def eta(self):
        return "-"

    def task(self):
        return self

    async def cancel_task(self):
        self.listener.is_cancelled = True
        await self.listener.on_upload_error("LuluStream upload cancelled!")
