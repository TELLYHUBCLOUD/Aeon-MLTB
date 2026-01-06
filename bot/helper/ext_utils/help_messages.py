from bot.core.aeon_client import TgClient
from bot.helper.telegram_helper.bot_commands import BotCommands

nsfw_keywords = [
    "fgjgfjgfhjgffgh",
]

mirror = """<blockquote expandable>╭ℹ️ <b>Mirror Help</b>
┊<b>Send link along with command line or </b>
┊
┊<code>/cmd link</code>
┊
┊<b>By replying to link/file</b>:
┊
┊<code>/cmd -n new name -e -up upload destination</code>
┊
┊<b>NOTE:</b>
╰1. Commands that start with <b>qb</b> are ONLY for torrents.</blockquote>"""

yt = """<blockquote expandable>╭ℹ️ <b>YouTube Help</b>
┊<b>Send link along with command line</b>:
┊
┊<code>/cmd link</code>
┊<b>By replying to link</b>:
┊<code>/cmd -n new name -z password -opt x:y|x1:y1</code>
┊
┊Check here all supported <a href='https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md'>SITES</a>
╰Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L212'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options."""

clone = """<blockquote expandable>╭ℹ️ <b>Clone Help</b>
┊Send Gdrive|Gdot|Filepress|Filebee|Appdrive|Gdflix link or rclone path along with command or by replying to the link/rc_path by command.
╰Use -sync to use sync method in rclone. Example: <code>/cmd rcl/rclone_path -up rcl/rclone_path/rc -sync</code>"""

new_name = """<blockquote expandable>╭ℹ️ <b>New Name</b>: -n
┊
┊<code>/cmd link -n new name</code>
╰Note: Doesn't work with torrents</blockquote>"""

multi_link = """<blockquote expandable>╭ℹ️ <b>Multi links only by replying to first link/file</b>: -i
┊
╰<code>/cmd -i 10(number of links/files)</code></blockquote>"""

same_dir = """<blockquote expandable>╭ℹ️ <b>Move file(s)/folder(s) to new folder</b>: -m
┊
┊You can use this arg also to move multiple links/torrents contents to the same directory, so all links will be uploaded together as one task
┊
┊<code>/cmd link -m new folder</code> (only one link inside new folder)
┊<code>/cmd -i 10(number of links/files) -m folder name</code> (all links contents in one folder)
┊<code>/cmd -b -m folder name</code> (reply to batch of message/file(each link on new line))
┊
┊While using bulk you can also use this arg with different folder name along with the links in message or file batch
┊Example:
┊link1 -m folder1
┊link2 -m folder1
┊link3 -m folder2
┊link4 -m folder2
┊link5 -m folder3
┊link6
┊so link1 and link2 content will be uploaded from same folder which is folder1
┊link3 and link4 content will be uploaded from same folder also which is folder2
┊link5 will uploaded alone inside new folder named folder3
╰link6 will get uploaded normally alone</blockquote>"""

thumb = """<blockquote expandable>╭ℹ️ <b>Thumbnail for current task</b>: -t
┊
╰<code>/cmd link -t tg-message-link</code> (doc or photo) or none (file without thumb)</blockquote>"""

split_size = """<blockquote expandable>╭ℹ️ <b>Split size for current task</b>: -sp
┊
┊<code>/cmd link -sp (500mb or 2gb or 4000000000)</code>
╰Note: Only mb and gb are supported or write in bytes without unit!</blockquote>"""

upload = """<blockquote expandable>╭ℹ️ <b>Upload Destination</b>: -up
┊
┊<code>/cmd link -up rcl/gdl</code> (rcl: to select rclone config, remote & path | gdl: To select token.pickle, gdrive id) using buttons
┊You can directly add the upload path: <code>-up remote:dir/subdir</code> or <code>-up Gdrive_id</code> or <code>-up id/username</code> (telegram) or <code>-up id/username|topic_id</code> (telegram)
┊If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
┊If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.
┊
┊If you want to add path or gdrive manually from your config/token (UPLOADED FROM USETTING) add mrcc: for rclone and mtp: before the path/gdrive_id without space.
┊<code>/cmd link -up mrcc:main:dump</code> or <code>-up mtp:gdrive_id</code> <strong>or you can simply edit upload using owner/user token/config from usetting without adding mtp: or mrcc: before the upload path/id</strong>
┊
┊To add leech destination:
┊<code>-up id/@username/pm</code>
┊<code>-up b:id/@username/pm</code> (b: means leech by bot) (id or username of the chat or write pm means private message so bot will send the files in private to you)
┊when you should use b:(leech by bot)? When your default settings is leech by user and you want to leech by bot for specific task.
┊<code>-up u:id/@username</code>(u: means leech by user) This incase OWNER added USER_SESSION_STRING.
┊<code>-up h:id/@username</code>(hybrid leech) h: to upload files by bot and user based on file size.
┊<code>-up id/@username|topic_id</code>(leech in specific chat and topic) add | without space and write topic id after chat id or username.
┊
┊In case you want to specify whether using token.pickle or service accounts you can add tp:gdrive_id (using token.pickle) or sa:gdrive_id (using service accounts) or mtp:gdrive_id (using token.pickle uploaded from usetting).
╰DEFAULT_UPLOAD doesn't affect on leech cmds.</blockquote>"""

user_download = """<blockquote expandable>╭ℹ️ <b>User Download</b>: link
┊
┊<code>/cmd tp:link</code> to download using owner token.pickle incase service account enabled.
┊<code>/cmd sa:link</code> to download using service account incase service account disabled.
┊<code>/cmd tp:gdrive_id</code> to download using token.pickle and file_id incase service account enabled.
┊<code>/cmd sa:gdrive_id</code> to download using service account and file_id incase service account disabled.
┊<code>/cmd mtp:gdrive_id</code> or <code>mtp:link</code> to download using user token.pickle uploaded from usetting
┊<code>/cmd mrcc:remote:path</code> to download using user rclone config uploaded from usetting
╰you can simply edit upload using owner/user token/config from usetting without adding mtp: or mrcc: before the path/id</blockquote>"""

rcf = """<blockquote expandable>╭ℹ️ <b>Rclone Flags</b>: -rcf
┊
┊<code>/cmd link|path|rcl -up path|rcl -rcf --buffer-size:8M|--drive-starred-only|key|key:value</code>
┊This will override all other flags except --exclude
╰Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>.</blockquote>"""

bulk = """<blockquote expandable>╭ℹ️ <b>Bulk Download</b>: -b
┊
┊Bulk can be used only by replying to text message or text file contains links separated by new line.
┊Example:
┊link1 -n new name -up remote1:path1 -rcf |key:value|key:value
┊link2 -z -n new name -up remote2:path2
┊link3 -e -n new name -up remote2:path2
┊Reply to this example by this cmd -> <code>/cmd -b(bulk)</code>
┊
┊Note: Any arg along with the cmd will be setted to all links
┊<code>/cmd -b -up remote: -z -m folder name</code> (all links contents in one zipped folder uploaded to one destination)
┊so you can't set different upload destinations along with link incase you have added -m along with cmd
┊You can set start and end of the links from the bulk like seed, with -b start:end or only end by -b :end or only start by -b start.
╰The default start is from zero(first link) to inf.</blockquote>"""

rlone_dl = """<blockquote expandable>╭ℹ️ <b>Rclone Download</b>:
┊
┊Treat rclone paths exactly like links
┊<code>/cmd main:dump/ubuntu.iso</code> or rcl(To select config, remote and path)
┊Users can add their own rclone from user settings
┊If you want to add path manually from your config add mrcc: before the path without space
┊<code>/cmd mrcc:main:dump/ubuntu.iso</code>
╰You can simply edit using owner/user config from usetting without adding mrcc: before the path</blockquote>"""

extract_zip = """<blockquote expandable>╭ℹ️ <b>Extract/Zip</b>: -e -z
┊
┊<code>/cmd link -e password</code> (extract password protected)
┊<code>/cmd link -z password</code> (zip password protected)
┊<code>/cmd link -z password -e</code> (extract and zip password protected)
╰Note: When both extract and zip added with cmd it will extract first and then zip, so always extract first</blockquote>"""

join = """<blockquote expandable>╭ℹ️ <b>Join Splitted Files</b>: -j
┊
┊This option will only work before extract and zip, so mostly it will be used with -m argument (samedir)
┊By Reply:
┊<code>/cmd -i 3 -j -m folder name</code>
┊<code>/cmd -b -j -m folder name</code>
┊if u have link(folder) have splitted files:
╰<code>/cmd link -j</code></blockquote>"""  

tg_links = """<blockquote expandable>╭ℹ️ <b>TG Links</b>:
┊
┊Treat links like any direct link
┊Some links need user access so you must add USER_SESSION_STRING for it.
┊Three types of links:
┊Public: <code>https://t.me/channel_name/message_id</code>
┊Private: <code>tg://openmessage?user_id=xxxxxx&message_id=xxxxx</code>
┊Super: <code>https://t.me/c/channel_id/message_id</code>
┊Range: <code>https://t.me/channel_name/first_message_id-last_message_id</code>
┊Range Example: <code>tg://openmessage?user_id=xxxxxx&message_id=555-560</code> or <code>https://t.me/channel_name/100-150</code>
╰Note: Range link will work only by replying cmd to it</blockquote>"""

sample_video = """<blockquote expandable>╭ℹ️ <b>Sample Video</b>: -sv
┊
┊Create sample video for one video or folder of videos.
┊<code>/cmd -sv</code> (it will take the default values which 60sec sample duration and part duration is 4sec).
╰You can control those values. Example: <code>/cmd -sv 70:5</code>(sample-duration:part-duration) or <code>/cmd -sv :5</code> or <code>/cmd -sv 70</code>.</blockquote>"""

screenshot = """<blockquote expandable>╭ℹ️ <b>ScreenShots</b>: -ss
┊
┊Create screenshots for one video or folder of videos.
┊<code>/cmd -ss</code> (it will take the default values which is 10 photos).
╰You can control this value. Example: <code>/cmd -ss 6</code>.</blockquote>"""

seed = """<blockquote expandable>╭ℹ️ <b>Bittorrent seed</b>: -d
┊
┊<code>/cmd link -d ratio:seed_time</code> or by replying to file/link
┊To specify ratio and seed time add <code>-d ratio:time</code>.
╰Example: <code>-d 0.7:10</code> (ratio and time) or <code>-d 0.7</code> (only ratio) or <code>-d :10</code> (only time) where time in minutes</blockquote>"""

zip_arg = """<blockquote expandable>╭ℹ️ <b>Zip</b>: -z password
┊
┊<code>/cmd link -z</code> (zip)
╰<code>/cmd link -z password</code> (zip password protected)</blockquote>"""

qual = """<blockquote expandable>╭ℹ️ <b>Quality Buttons</b>: -s
┊
┊In case default quality added from yt-dlp options using format option and you need to select quality for specific link or links with multi links feature.
╰<code>/cmd link -s</code></blockquote>"""

yt_opt = """<blockquote expandable>╭ℹ️ <b>Options</b>: -opt
┊
┊<code>/cmd link -opt {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}</code>
╰Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.</blockquote>"""

convert_media = """<blockquote expandable>╭ℹ️ <b>Convert Media</b>: -ca -cv
┊<code>/cmd link -ca mp3 -cv mp4</code> (convert all audios to mp3 and all videos to mp4)
┊<code>/cmd link -ca mp3</code> (convert all audios to mp3)
┊<code>/cmd link -cv mp4</code> (convert all videos to mp4)
┊<code>/cmd link -ca mp3 + flac ogg</code> (convert only flac and ogg audios to mp3)
╰<code>/cmd link -cv mkv - webm flv</code> (convert all videos to mp4 except webm and flv)</blockquote>"""

force_start = """<blockquote expandable>╭ℹ️ <b>Force Start</b>: -f -fd -fu
┊<code>/cmd link -f</code> (force download and upload)
┊<code>/cmd link -fd</code> (force download only)
╰<code>/cmd link -fu</code> (force upload directly after download finish)</blockquote>"""

gdrive = """<blockquote expandable>╭ℹ️ <b>Gdrive</b>: link
┊If DEFAULT_UPLOAD is `rc` then you can pass up: `gd` to upload using gdrive tools to GDRIVE_ID.
┊<code>/cmd gdriveLink</code> or <code>gdl</code> or <code>gdriveId</code> -up <code>gdl</code> or <code>gdriveId</code> or <code>gd</code>
┊<code>/cmd tp:gdriveLink</code> or <code>tp:gdriveId</code> -up <code>tp:gdriveId</code> or <code>gdl</code> or <code>gd</code> (to use token.pickle if service account enabled)
┊<code>/cmd sa:gdriveLink</code> or <code>sa:gdriveId</code> -p <code>sa:gdriveId</code> or <code>gdl</code> or <code>gd</code> (to use service account if service account disabled)
┊<code>/cmd mtp:gdriveLink</code> or <code>mtp:gdriveId</code> -up <code>mtp:gdriveId</code> or <code>gdl</code> or <code>gd</code>(if you have added upload gdriveId from usetting) (to use user token.pickle that uploaded by usetting)
╰You can simply edit using owner/user token from usetting without adding mtp: before the id</blockquote>"""

rclone_cl = """<blockquote expandable>╭ℹ️ <b>Rclone</b>: path
┊If DEFAULT_UPLOAD is `gd` then you can pass up: `rc` to upload to RCLONE_PATH.
┊<code>/cmd rcl/rclone_path -up rcl/rclone_path/rc -rcf flagkey:flagvalue|flagkey|flagkey:flagvalue</code>
┊<code>/cmd rcl</code> or <code>rclone_path</code> -up <code>rclone_path</code> or <code>rc</code> or <code>rcl</code>
╰<code>/cmd mrcc:rclone_path</code> -up <code>rcl</code> or <code>rc</code>(if you have add rclone path from usetting) (to use user config)</blockquote>"""

name_sub = r"""<blockquote expandable>╭ℹ️ <b>Name Substitution</b>: -ns
┊<code>/cmd link -ns script/code/s | mirror/leech | tea/ /s | clone | cpu/ | \[hello\]/hello | \\text\\/text/s</code>
┊This will affect on all files. Format: wordToReplace/wordToReplaceWith/sensitiveCase
┊Word Subtitions. You can add pattern instead of normal text. Timeout: 60 sec
┊NOTE: You must add \ before any character, those are the characters: \^$.|?*+()[]{}-
┊1. script will get replaced by code with sensitive case
┊2. mirror will get replaced by leech
┊4. tea will get replaced by space with sensitive case
┊5. clone will get removed
┊6. cpu will get replaced by space
┊7. [hello] will get replaced by hello
╰8. \text\ will get replaced by text with sensitive case</blockquote>"""

transmission = """<blockquote expandable>╭ℹ️ <b>Tg transmission</b>: -hl -ut -bt
┊<code>/cmd link -hl</code> (leech by user and bot session with respect to size) (Hybrid Leech)
┊<code>/cmd link -bt</code> (leech by bot session)
╰<code>/cmd link -ut</code> (leech by user)</blockquote>"""

thumbnail_layout = """<blockquote expandable>╭ℹ️ <b>Thumbnail Layout</b>: -tl
╰<code>/cmd link -tl 3x3</code> (widthxheight) 3 photos in row and 3 photos in column</blockquote>"""

leech_as = """<blockquote expandable>╭ℹ️ <b>Leech as</b>: -doc -med
┊<code>/cmd link -doc</code> (Leech as document)
╰<code>/cmd link -med</code> (Leech as media)</blockquote>"""

ffmpeg_cmds = """<blockquote expandable>╭ℹ️ <b>FFmpeg Commands</b>: -ff
┊list of lists of ffmpeg commands. You can set multiple ffmpeg commands for all files before upload. Don't write ffmpeg at beginning, start directly with the arguments.
┊Notes:
┊1. Add <code>-del</code> to the list(s) which you want from the bot to delete the original files after command run complete!
┊2. To execute one of pre-added lists in bot like: ({"subtitle": ["-i mltb.mkv -c copy -c:s srt mltb.mkv"]}), you must use <code>-ff subtitle</code> (list key)
┊Examples: <code>["-i mltb.mkv -c copy -c:s srt mltb.mkv", "-i mltb.video -c copy -c:s srt mltb", "-i mltb.m4a -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb.audio -c:a libmp3lame -q:a 2 mltb.mp3", "-i mltb -map 0:a -c copy mltb.mka -map 0:s -c copy mltb.srt", "-i mltb -i tg://openmessage?user_id=5272663208&message_id=322801 -filter_complex 'overlay=W-w-10:H-h-10' -c:a copy mltb"]</code>
┊Here I will explain how to use mltb.* which is reference to files you want to work on.
┊1. First cmd: the input is mltb.mkv so this cmd will work only on mkv videos and the output is mltb.mkv also so all outputs is mkv. -del will delete the original media after complete run of the cmd.
┊2. Second cmd: the input is mltb.video so this cmd will work on all videos and the output is only mltb so the extenstion is same as input files.
┊3. Third cmd: the input in mltb.m4a so this cmd will work only on m4a audios and the output is mltb.mp3 so the output extension is mp3.
┊4. Fourth cmd: the input is mltb.audio so this cmd will work on all audios and the output is mltb.mp3 so the output extension is mp3.
╰5. Fifth cmd: You can add telegram link for small size input like photo to set watermark</blockquote>"""

YT_HELP_DICT = {
    "main": yt,
    "New-Name": f"{new_name}\nNote: Don't add file extension",
    "Zip": zip_arg,
    "Quality": qual,
    "Options": yt_opt,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
    "Convert-Media": convert_media,
    "Force-Start": force_start,
    "Name-Substitute": name_sub,
    "TG-Transmission": transmission,
    "Thumb-Layout": thumbnail_layout,
    "Leech-Type": leech_as,
    "FFmpeg-Cmds": ffmpeg_cmds,
}

MIRROR_HELP_DICT = {
    "main": mirror,
    "New-Name": new_name,
    "DL-Auth": "<b>Direct link authorization</b>: -au -ap\n\n/cmd link -au username -ap password",
    "Headers": "<b>Direct link custom headers</b>: -h\n\n/cmd link -h key:value|key1:value1",
    "Extract/Zip": extract_zip,
    "Select-Files": "<b>Bittorrent/JDownloader/Sabnzbd File Selection</b>: -s\n\n/cmd link -s or by replying to file/link",
    "Torrent-Seed": seed,
    "Multi-Link": multi_link,
    "Same-Directory": same_dir,
    "Thumb": thumb,
    "Split-Size": split_size,
    "Upload-Destination": upload,
    "Rclone-Flags": rcf,
    "Bulk": bulk,
    "Join": join,
    "Rclone-DL": rlone_dl,
    "Tg-Links": tg_links,
    "Sample-Video": sample_video,
    "Screenshot": screenshot,
    "Convert-Media": convert_media,
    "Force-Start": force_start,
    "User-Download": user_download,
    "Name-Substitute": name_sub,
    "TG-Transmission": transmission,
    "Thumb-Layout": thumbnail_layout,
    "Leech-Type": leech_as,
    "FFmpeg-Cmds": ffmpeg_cmds,
}

CLONE_HELP_DICT = {
    "main": clone,
    "Multi-Link": multi_link,
    "Bulk": bulk,
    "Gdrive": gdrive,
    "Rclone": rclone_cl,
}

RSS_HELP_MESSAGE = """<blockquote expandable>╭ℹ️ <b>RSS Help</b>
┊Use this format to add feed url:
┊Title1 link (required)
┊Title2 link -c cmd -inf xx -exf xx
┊Title3 link -c cmd -d ratio:time -z password
┊
┊-c command -up mrcc:remote:path/subdir -rcf --buffer-size:8M|key|key:value
┊-inf For included words filter.
┊-exf For excluded words filter.
┊-stv true or false (sensitive filter)
┊
┊Example: Title https://www.rss-url.com -inf 1080 or 720 or 144p|mkv or mp4|hevc -exf flv or web|xxx
┊This filter will parse links that its titles contain `(1080 or 720 or 144p) and (mkv or mp4) and hevc` and doesn't contain (flv or web) and xxx words. You can add whatever you want.
┊
┊Another example: -inf  1080  or 720p|.web. or .webrip.|hvec or x264. This will parse titles that contain ( 1080  or 720p) and (.web. or .webrip.) and (hvec or x264). I have added space before and after 1080 to avoid wrong matching. If this `10805695` number in title it will match 1080 if added 1080 without spaces after it.
┊
┊Filter Notes:
┊1. | means and.
┊2. Add `or` between similar keys, you can add it between qualities or between extensions, so don't add filter like this f: 1080|mp4 or 720|web because this will parse 1080 and (mp4 or 720) and web ... not (1080 and mp4) or (720 and web).
┊3. You can add `or` and `|` as much as you want.
┊4. Take a look at the title if it has a static special character after or before the qualities or extensions or whatever and use them in the filter to avoid wrong match.
╰Timeout: 60 sec.</blockquote>"""

PASSWORD_ERROR_MESSAGE = """<blockquote expandable>╭❌ <b>Password Error</b>
┊<b>This link requires a password!</b>
┊- Insert <b>::</b> after the link and write the password after the sign.
╰<b>Example:</b> link::my password</blockquote>""" 


user_settings_text = {
    "METADATA_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your text for change mkv medias metadata (title only). Timeout: 60 sec</blockquote>",
    "WATERMARK_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your text which will added as watermark in all mkv videos left upper corner. Timeout: 60 sec</blockquote>",
    "USER_SESSION": "╭ℹ️ <b>Info</b>\n╰Send your pyrogram user session string for download from private telegram chat. Timeout: 60 sec",
    "USER_DUMP": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your channel or group id where you want to store your leeched files. Bot must have permission to send message in your chat. Timeout: 60 sec</blockquote>",
    "LEECH_FILENAME_CAPTION": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send leech filename caption. Timeout: 60 sec</blockquote>",
    "LEECH_SPLIT_SIZE": f"<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Leech split size in bytes or use gb or mb. Example: 40000000 or 2.5gb or 1000mb. IS_PREMIUM_USER: {TgClient.IS_PREMIUM_USER}. Timeout: 60 sec</blockquote>",
    "LEECH_FILENAME_PREFIX": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Leech Filename Prefix. You can add HTML tags. Example: <code>@mychannel</code>. Timeout: 60 sec</blockquote>",
    "LEECH_FILENAME_SUFFIX": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Leech Filename Suffix. You can add HTML tags. Example: <code>@mychannel</code>. Timeout: 60 sec</blockquote>",
    "LEECH_CAPTION_FONT": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Font Name. Available fonts: bold, italic, code, underline. Example: <code>bold</code>. Timeout: 60 sec</blockquote>",
    "FILENAME_REPLACE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send filename replace rules. Format: <code>old:new|word</code>. Example: <code>mkv:mp4|@username</code>. Timeout: 60 sec</blockquote>",
    "THUMBNAIL_LAYOUT": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send thumbnail layout (widthxheight, 2x2, 3x3, 2x4, 4x4, ...). Example: 3x3. Timeout: 60 sec</blockquote>",
    "RCLONE_PATH": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Rclone Path. If you want to use your rclone config edit using owner/user config from usetting or add mrcc: before rclone path. Example mrcc:remote:folder. Timeout: 60 sec</blockquote>",
    "RCLONE_FLAGS": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰key:value|key|key|key:value . Check here all <a href='https://rclone.org/flags/'>RcloneFlags</a>\nEx: --buffer-size:8M|--drive-starred-only</blockquote>",
    "GDRIVE_ID": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Gdrive ID. If you want to use your token.pickle edit using owner/user token from usetting or add mtp: before the id. Example: mtp:F435RGGRDXXXXXX . Timeout: 60 sec</blockquote>",
    "INDEX_URL": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Index URL. Timeout: 60 sec</blockquote>",
    "UPLOAD_PATHS": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send Dict of keys that have path values. Example: {'path 1': 'remote:rclonefolder', 'path 2': 'gdrive1 id', 'path 3': 'tg chat id', 'path 4': 'mrcc:remote:', 'path 5': b:@username} . Timeout: 60 sec</blockquote>",
    "EXCLUDED_EXTENSIONS": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send exluded extenions separated by space without dot at beginning. Timeout: 60 sec</blockquote>",
    "NAME_SUBSTITUTE": r"""<blockquote expandable>╭ℹ️ <b>Info</b>
┊Word Substitutions. You can add pattern instead of normal text. Timeout: 60 sec
┊<b>NOTE:</b> You must add \ before any character, those are the characters: \^$.|?*+()[]{}-
┊<b>Example:</b> script/code/s | mirror/leech | tea/ /s | clone | cpu/ | \[mltb\]/mltb | \\text\\/text/s
┊1. script will get replaced by code with sensitive case
┊2. mirror will get replaced by leech
┊4. tea will get replaced by space with sensitive case
┊5. clone will get removed
┊6. cpu will get replaced by space
┊7. [mltb] will get replaced by mltb
┊8. \text\ will get replaced by text with sensitive case</blockquote>""",
    "YT_DLP_OPTIONS": """<blockquote expandable>╭ℹ️ <b>Info</b>
┊Send dict of YT-DLP Options. Timeout: 60 sec
┊<b>Format:</b> {key: value, key: value, key: value}.
┊<b>Example:</b> {"format": "bv*+mergeall[vcodec=none]", "nocheckcertificate": True, "playliststart": 10, "fragment_retries": float("inf"), "matchtitle": "S13", "writesubtitles": True, "live_from_start": True, "postprocessor_args": {"ffmpeg": ["-threads", "4"]}, "wait_for_video": (5, 100), "download_ranges": [{"start_time": 0, "end_time": 10}]}
╰Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.</blockquote>""",
    
    "FFMPEG_CMDS": """<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Read this guide. http://telegra.ph/Ffmpeg-guide-01-10</blockquote>""",
    "YT_DEFAULT_CATEGORY": """<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Set your default YouTube video category ID (e.g., 22 for People & Blogs). Timeout: 60 sec</blockquote>""",
    "YT_DEFAULT_TAGS": """<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Set your default YouTube tags, separated by commas. Timeout: 60 sec</blockquote>""",
    "YT_DEFAULT_PRIVACY": """<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Set your default YouTube upload privacy (public, private, unlisted). Timeout: 60 sec</blockquote>""",
    "YT_DEFAULT_DESCRIPTION": """<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Set your default YouTube video description. Timeout: 60 sec</blockquote>""",
    "YT_DEFAULT_FOLDER_MODE": """<blockquote expandable>╭ℹ️ <b>Info</b>
┊Choose how folders (containing multiple videos) are uploaded to YouTube by default:
┊- <b>Playlist</b>: Uploads the entire folder as a single new YouTube playlist.
┊- <b>Individual Videos</b>: Uploads each video from the folder as an individual YouTube video, without creating a playlist.
┊- <b>Playlist & Individuals</b>: Uploads the folder as a new playlist AND also makes each video available individually.
╰Timeout: 60 sec</blockquote>""",
    "YT_ADD_TO_PLAYLIST_ID": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Enter the YouTube Playlist ID you want your videos to be added to. If set, newly uploaded videos will be added to this playlist. Leave empty or set to 'None' to not automatically add to a specific playlist (unless creating a new one for a folder upload without this setting). Timeout: 60 sec</blockquote>",
    "GOFILE_TOKEN": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your GoFile API token. You can get it from https://gofile.io/myProfile. This token will be used to upload files to your GoFile account. Timeout: 60 sec</blockquote>",
    "GOFILE_FOLDER_ID": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your GoFile folder ID where you want to upload files. If not set, files will be uploaded to your account root. You can get folder ID from the GoFile URL. Example: for https://gofile.io/d/abcd123, the folder ID is abcd123. Timeout: 60 sec</blockquote>",
    "BUZZHEAVIER_TOKEN": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your Buzzheavier API token. You can get it from your Buzzheavier account settings. This token will be used to upload files to your Buzzheavier account. Timeout: 60 sec</blockquote>",
    "BUZZHEAVIER_FOLDER_ID": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your Buzzheavier folder ID where you want to upload files. If not set, files will be uploaded to your account root. Timeout: 60 sec</blockquote>",
    "PIXELDRAIN_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your Pixeldrain API key. You can get it from your Pixeldrain account settings. This key will be used to upload files to your Pixeldrain account. Timeout: 60 sec</blockquote>",
    "AUTO_LEECH_CMD": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your default Leech command (e.g., <code>leech</code> or <code>yl</code> or <code>pleech</code>). Timeout: 60 sec</blockquote>",
    "AUTO_MIRROR_CMD": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your default Mirror command (e.g., <code>mirror</code> or <code>um</code>). Timeout: 60 sec</blockquote>",
    "AUTO_COMPRESS_CMD": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your default FFmpeg command to be appended to leech commands automatically. Example: -ff -metadata title='My Title'. Timeout: 60 sec</blockquote>",
    "AUTO_CAPTION_REPLACE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your caption replacement rules. Format: old1:new1|old2:new2. Case-insensitive. Timeout: 60 sec</blockquote>",
    "AUTO_CAPTION_REMOVE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send keywords to remove from captions. Format: word1|word2|word3 or re:regex_pattern. Case-insensitive. Timeout: 60 sec</blockquote>",
    "LULU_API_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your LuluStream API Key. You can get it from your LuluStream account settings. Timeout: 60 sec</blockquote>",
    "TMDB_API_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your TMDB API key to enable auto thumbnail fetching.\n\nGet your free API key from: https://www.themoviedb.org/settings/api\n\nTimeout: 60 sec</blockquote>",
    "AUTO_THUMBNAIL_FORMAT": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send thumbnail format for auto thumbnails:\n\n• <code>poster</code> - Movie/TV show poster (default)\n• <code>backdrop</code> - Background/scene image\n\nTimeout: 60 sec</blockquote>",
    "AUTO_RENAME_TEMPLATE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send rename template for auto renaming. Available variables: {season}, {episode}, {quality}, {title}\n\nExample: <code>S{season}E{episode}Q{quality}</code>\n\nTimeout: 60 sec</blockquote>",
    "AUTO_RENAME_START_EPISODE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send starting episode number for auto renaming (default: 1). Timeout: 60 sec</blockquote>",
    "AUTO_RENAME_START_SEASON": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send starting season number for auto renaming (default: 1). Timeout: 60 sec</blockquote>",
    "LEECH_SPLIT_SIZE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the size to split leech files. Format: 2GB or 4GB or 2000MB. Timeout: 60 sec</blockquote>",
    "THUMBNAIL_LAYOUT": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the thumbnail layout (e.g., 2x2, 3x3). Timeout: 60 sec</blockquote>",
    "USER_DUMP": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the chat ID or username where you want the bot to dump leeches. Timeout: 60 sec</blockquote>",
    "USER_SESSION": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send your Pyrogram Session String for user account leeching. Timeout: 60 sec</blockquote>",
    "EXCLUDED_EXTENSIONS": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send extensions to exclude from leeching/mirroring, separated by space. Timeout: 60 sec</blockquote>",
    "UPLOAD_PATHS": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send dict of upload paths for different hosters.\n<b>Format:</b> {'gd': 'path', 'rc': 'path'}. Timeout: 60 sec</blockquote>",
    "NAME_SUBSTITUTE": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send name substitution rules. Format: old1:new1|old2:new2. Timeout: 60 sec</blockquote>",
    "WATERMARK_KEY": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the text for watermark. Timeout: 60 sec</blockquote>",
    "LEECH_CAPTION_FONT": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the font style for leech caption (e.g., bold, italic, code). Timeout: 60 sec</blockquote>",
    "METADATA": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the metadata text to be added to files. Timeout: 60 sec</blockquote>",
    "AUDIO_METADATA": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the audio metadata text. Timeout: 60 sec</blockquote>",
    "VIDEO_METADATA": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the video metadata text. Timeout: 60 sec</blockquote>",
    "SUBTITLE_METADATA": "<blockquote expandable>╭ℹ️ <b>Info</b>\n╰Send the subtitle metadata text. Timeout: 60 sec</blockquote>",
}

merge_help_main = """<blockquote expandable>╭ℹ️ <b>Merge Help</b>
┊<b>Send multiple links/files to merge them into one video.</b>
┊
┊<b>Usage:</b>
┊<code>/merge link1 link2 link3</code> (Max 10 inputs)
┊
┊<b>By replying to a message with links</b>:
┊Reply to a message containing links (one per line) with <code>/merge -b</code>
┊
┊<b>Smart Renaming (Analysis):</b>
┊Bot will auto-detect series name and episodes from filenames (e.g., "Show S01E01") and rename output like "Show S01E01-E10".
┊
┊<b>NOTE:</b>
┊1. All inputs will be concatenated in order.
┊2. If 'ass' subtitles are detected, output will automatically be '.mkv'.
╰3. Downloads are processed sequentially to ensure stability.</blockquote>"""





MERGE_HELP_DICT = {
    "main": merge_help_main,
    "inputs": multi_link, # Reusing multi_link help
    "upload": upload,
    "new_name": new_name,
    "thumbnail": thumb,
    "split_size": split_size,
}



automation_help_main = """<blockquote expandable>╭ℹ️ <b>Automation Help</b>
┊<b>Automate your leeching tasks with these settings.</b>
┊
┊<b>To access these settings:</b>
┊<code>/userset</code> -> <b>🤖 Auto Features</b>
┊
┊<b>Features:</b>
┊1. <b>Auto Leech</b>: Automatically mirror/leech links sent to the bot (forwarded or direct).
┊2. <b>Auto Leech Cmd</b>: The default command to use (e.g., <code>/leech</code>, <code>/mirror</code>, <code>/yl</code>).
┊3. <b>Auto Compress Cmd</b>: Extra arguments to append (e.g., <code>-z password</code>, <code>-ff</code>).
┊4. <b>Auto Caption</b>: Replace or remove parts of filenames/captions.
╰Check specific help buttons for more details.</blockquote>"""

AUTOMATION_HELP_DICT = {
    "main": automation_help_main,
    "Auto-Leech": "<b>Auto Leech</b>\n\nEnable this to let the bot automatically process links sent to it in private chat.\nNote: Requires <code>Auto Leech Cmd</code> to be set.",
    "Auto-Leech-Cmd": user_settings_text["AUTO_LEECH_CMD"],
    "Auto-Compress-Cmd": user_settings_text["AUTO_COMPRESS_CMD"],
    "Caption-Replace": user_settings_text["AUTO_CAPTION_REPLACE"],
    "Caption-Remove": user_settings_text["AUTO_CAPTION_REMOVE"],
}

help_string = f"""<blockquote expandable>╭ℹ️ <b>Help Guide</b>
┊NOTE: Try each command without any argument to see more detalis.
┊/{BotCommands.MirrorCommand[0]} or /{BotCommands.MirrorCommand[1]}: Start mirroring to cloud.
┊/{BotCommands.JdMirrorCommand[0]} or /{BotCommands.JdMirrorCommand[1]}: Start Mirroring to cloud using JDownloader.
┊/{BotCommands.NzbMirrorCommand[0]} or /{BotCommands.NzbMirrorCommand[1]}: Start Mirroring to cloud using Sabnzbd.
┊/{BotCommands.YtdlCommand[0]} or /{BotCommands.YtdlCommand[1]}: Mirror yt-dlp supported link.
┊/{BotCommands.LeechCommand[0]} or /{BotCommands.LeechCommand[1]}: Start leeching to Telegram.
┊/{BotCommands.JdLeechCommand[0]} or /{BotCommands.JdLeechCommand[1]}: Start leeching using JDownloader.
┊/{BotCommands.NzbLeechCommand[0]} or /{BotCommands.NzbLeechCommand[1]}: Start leeching using Sabnzbd.
┊/{BotCommands.YtdlLeechCommand[0]} or /{BotCommands.YtdlLeechCommand[1]}: Leech yt-dlp supported link.
┊/{BotCommands.MergeCommand} [link]: Merge video files.
┊/{BotCommands.CloneCommand} [drive_url]: Copy file/folder to Google Drive.
┊/{BotCommands.CountCommand} [drive_url]: Count file/folder of Google Drive.
┊/{BotCommands.DeleteCommand} [drive_url]: Delete file/folder from Google Drive (Only Owner & Sudo).
┊/{BotCommands.UserSetCommand} [query]: Users settings.
┊/{BotCommands.BotSetCommand} [query]: Bot settings.
┊/{BotCommands.SelectCommand}: Select files from torrents by gid or reply.
┊/{BotCommands.ForceStartCommand[0]} or /{BotCommands.ForceStartCommand[1]} [gid]: Force start task by gid or reply.
┊/{BotCommands.CancelAllCommand} [query]: Cancel all [status] tasks.
┊/{BotCommands.ListCommand} [query]: Search in Google Drive(s).
┊/{BotCommands.SearchCommand} [query]: Search for torrents with API.
┊/{BotCommands.StatusCommand[0]}: Shows a status of all the downloads.
┊/{BotCommands.StatusCommand[0]}: Shows a status of all the downloads.
┊/{BotCommands.StatsCommand}: Show stats of the machine where the bot is hosted in.
╰/automation: Show help guide for Automation features.</blockquote>"""

