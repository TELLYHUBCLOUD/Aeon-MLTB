from bot.helper.ext_utils.status_utils import MirrorStatus, get_readable_file_size, get_readable_time

class LuluStatus:
    def __init__(self, listener, obj, status):
        self.listener = listener
        self._obj = obj
        self._status = status
        self.tool = getattr(obj, "tool", "Uploader")

    def gid(self):
        return self.listener.mid

    def name(self):
        return self.listener.name

    def size(self):
        return get_readable_file_size(self.listener.size)

    def status(self):
        return MirrorStatus.STATUS_UPLOAD

    def processed_bytes(self):
        if hasattr(self._obj, "processed_bytes"):
            return self._obj.processed_bytes
        return getattr(self.listener, "processed_bytes", 0)

    def progress(self):
        try:
            return f"{(self.processed_bytes() / self.listener.size) * 100:.2f}%"
        except Exception:
            return "0%"

    def speed(self):
        speed = getattr(self._obj, "speed", 0)
        return f"{get_readable_file_size(speed)}/s"

    def eta(self):
        try:
            speed = getattr(self._obj, "speed", 0)
            if speed > 0:
                seconds = (self.listener.size - self.processed_bytes()) / speed
                return get_readable_time(seconds)
        except Exception:
            pass
        return "-"

    def task(self):
        return self

    async def cancel_task(self):
        self.listener.is_cancelled = True
        if hasattr(self._obj, "cancel_task"):
            await self._obj.cancel_task()
        else:
            await self.listener.on_upload_error(f"{self.tool} upload cancelled!")
