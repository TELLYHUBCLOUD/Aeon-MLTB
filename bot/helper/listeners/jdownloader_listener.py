from asyncio import sleep

from bot import intervals, jd_downloads, jd_listener_lock
from bot.core.jdownloader_booter import jdownloader
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.status_utils import get_task_by_gid


@new_task
async def remove_download(gid):
    if intervals["stopAll"]:
        return
    await jdownloader.device.downloads.remove_links(
        package_ids=jd_downloads[gid]["ids"],
    )
    if task := await get_task_by_gid(gid):
        await task.listener.on_download_error("Download removed manually!")
        async with jd_listener_lock:
            del jd_downloads[gid]


@new_task
async def _on_download_complete(gid):
    if task := await get_task_by_gid(gid):
        if task.listener.select:
            async with jd_listener_lock:
                await jdownloader.device.downloads.cleanup(
                    "DELETE_DISABLED",
                    "REMOVE_LINKS_AND_DELETE_FILES",
                    "ALL",
                    package_ids=jd_downloads[gid]["ids"],
                )
        
        # Fix for HLS downloads without extensions
        # JDownloader downloads HLS streams but doesn't add proper file extensions
        # This causes "No files to upload" error during leech
        try:
            from os import walk, rename
            from os.path import splitext, join
            
            download_path = jd_downloads[gid]["path"]
            for dirpath, _, files in walk(download_path):
                for file in files:
                    file_path = join(dirpath, file)
                    name, ext = splitext(file)
                    
                    # If file has no extension, add .mp4 (common for HLS streams)
                    if not ext:
                        new_path = f"{file_path}.mp4"
                        rename(file_path, new_path)
                        from bot import LOGGER
                        LOGGER.info(f"Added .mp4 extension to HLS file: {file} -> {file}.mp4")
        except Exception as e:
            from bot import LOGGER
            LOGGER.error(f"Error adding extension to JD files: {e}")
        
        await task.listener.on_download_complete()
        if intervals["stopAll"]:
            return
        async with jd_listener_lock:
            if gid in jd_downloads:
                await jdownloader.device.downloads.remove_links(
                    package_ids=jd_downloads[gid]["ids"],
                )
                del jd_downloads[gid]


@new_task
async def _jd_listener():
    while True:
        await sleep(3)
        async with jd_listener_lock:
            if len(jd_downloads) == 0:
                intervals["jd"] = ""
                break
            try:
                packages = await jdownloader.device.downloads.query_packages(
                    [{"finished": True, "saveTo": True}],
                )
            except Exception:
                continue

            all_packages = {pack["uuid"]: pack for pack in packages}
            for d_gid, d_dict in list(jd_downloads.items()):
                if d_dict["status"] == "down":
                    for index, pid in enumerate(d_dict["ids"]):
                        if pid not in all_packages:
                            del jd_downloads[d_gid]["ids"][index]
                    if len(jd_downloads[d_gid]["ids"]) == 0:
                        path = jd_downloads[d_gid]["path"]
                        jd_downloads[d_gid]["ids"] = [
                            uid
                            for uid, pk in all_packages.items()
                            if pk["saveTo"].startswith(path)
                        ]
                    if len(jd_downloads[d_gid]["ids"]) == 0:
                        await remove_download(d_gid)

            if completed_packages := [
                pack["uuid"] for pack in packages if pack.get("finished", False)
            ]:
                for d_gid, d_dict in list(jd_downloads.items()):
                    if d_dict["status"] == "down":
                        is_finished = all(
                            did in completed_packages for did in d_dict["ids"]
                        )
                        if is_finished:
                            jd_downloads[d_gid]["status"] = "done"
                            await _on_download_complete(d_gid)


async def on_download_start():
    async with jd_listener_lock:
        if not intervals["jd"]:
            intervals["jd"] = await _jd_listener()
