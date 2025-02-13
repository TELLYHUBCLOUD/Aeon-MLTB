from bot.helper.telegram_helper.bot_commands import BotCommands

nsfw_keywords = [
    "porn",
    "onlyfans",
    "nsfw",
    "Brazzers",
    "adult",
    "xnxx",
    "xvideos",
    "nsfwcherry",
    "hardcore",
    "Pornhub",
    "xvideos2",
    "youporn",
    "pornrip",
    "playboy",
    "hentai",
    "erotica",
    "blowjob",
    "redtube",
    "stripchat",
    "camgirl",
    "nude",
    "fetish",
    "cuckold",
    "orgy",
    "horny",
    "swingers",
    "ullu",
]

mirror = """📤 <b>Mirror Command</b>
<blockquote>
<b>Send link along with command line or </b>

/cmd link

<b>By replying to link/file</b>:

/cmd -n new name -e -up upload destination

<b>NOTE:</b>
1. Commands that start with <b>qb</b> are ONLY for torrents.
</blockquote>"""

yt = """🎥 <b>YT-DLP Command</b>
<blockquote>
<b>Send link along with command line</b>:

/cmd link
<b>By replying to link</b>:
/cmd -n new name -z password -opt x:y|x1:y1

Check here all supported <a href='https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md'>SITES</a>
Check all yt-dlp api options from this <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L212'>FILE</a> or use this <a href='https://t.me/mltb_official_channel/177'>script</a> to convert cli arguments to api options.
</blockquote>"""

clone = """🔗 <b>Clone Command</b>
<blockquote>
Send Gdrive|Gdot|Filepress|Filebee|Appdrive|Gdflix link or rclone path along with command or by replying to the link/rc_path by command.
Use -sync to use sync method in rclone. Example: /cmd rcl/rclone_path -up rcl/rclone_path/rc -sync
</blockquote>"""

new_name = """📝 <b>New Name</b>
<blockquote>
Use -n option to set custom name

<code>/cmd link -n new name</code>
Note: Doesn't work with torrents
</blockquote>"""

multi_link = """🔢 <b>Multi Links</b>
<blockquote>
Process multiple links at once by replying to first link/file with -i

<code>/cmd -i 10</code> (number of links/files)
</blockquote>"""

same_dir = """📁 <b>Same Directory</b>
<blockquote>
Use -m to move files to common folder

<code>/cmd link -m folder_name</code>
Combine with -i for multiple links:
<code>/cmd -i 10 -m folder_name</code>
</blockquote>"""

thumb = """🖼️ <b>Custom Thumbnail</b>
<blockquote>
Set thumbnail using -t option

<code>/cmd link -t tg-photo-link</code> or <code>none</code> to remove
</blockquote>"""

split_size = """✂️ <b>Split Files</b>
<blockquote>
Split archives with -sp option

<code>/cmd link -sp 500mb</code> or <code>2gb</code>
</blockquote>"""

upload = """📤 <b>Upload Settings</b>
<blockquote>
Set destination with -up option

<code>/cmd link -up rcl/gdl</code> (via buttons)
Direct path: <code>-up remote:path</code> or <code>gdrive_id</code>
Add prefixes: <code>mrcc:</code> or <code>mtp:</code> for custom configs
</blockquote>"""

user_download = """👤 <b>User Download</b>
<blockquote>
Specify download method with prefixes:

<code>/cmd tp:link</code> - Token.pickle
<code>/cmd sa:link</code> - Service Account
<code>/cmd mtp:link</code> - User's Token
</blockquote>"""

rcf = """🚩 <b>Rclone Flags</b>
<blockquote>
Add custom flags with -rcf

<code>/cmd link -rcf --buffer-size:8M|--drive-starred-only</code>
Check <a href='https://rclone.org/flags/'>all flags</a>
</blockquote>"""

bulk = """📦 <b>Bulk Operations</b>
<blockquote>
Process multiple links from file/message

<code>/cmd -b</code> (reply to file/message)
Specify range: <code>-b 5:10</code>
Combine with other options: <code>-b -m folder</code>
</blockquote>"""

rlone_dl = """🔄 <b>Rclone Download</b>
<blockquote>
Download from rclone paths directly

<code>/cmd main:dump/file.iso</code>
Use <code>mrcc:</code> prefix for custom configs
</blockquote>"""

extract_zip = """📦 <b>Archive Tools</b>
<blockquote>
Extract/zip files with -e/-z

<code>/cmd link -e password</code> (extract)
<code>/cmd link -z password</code> (zip)
Combine both: <code>-z pass -e</code>
</blockquote>"""

join = """🧩 <b>Join Files</b>
<blockquote>
Merge split files with -j

<code>/cmd -i 3 -j -m folder</code>
Works with bulk: <code>/cmd -b -j</code>
</blockquote>"""

tg_links = """📨 <b>Telegram Links</b>
<blockquote>
Handle Telegram content directly

Supports public/private/super links
Format: <code>https://t.me/c/channel_id/message_id</code>
Ranges: <code>https://t.me/channel/100-150</code>
</blockquote>"""

sample_video = """🎞️ <b>Sample Video</b>
<blockquote>
Create previews with -sv

<code>/cmd -sv 60:5</code> (60s sample, 5s parts)
Default: <code>/cmd -sv</code> (60:4)
</blockquote>"""

screenshot = """📸 <b>Screenshots</b>
<blockquote>
Generate images with -ss

<code>/cmd -ss 8</code> (8 screenshots)
Default: <code>/cmd -ss</code> (10 screenshots)
</blockquote>"""

seed = """🌱 <b>Torrent Seeding</b>
<blockquote>
Control seeding with -d

<code>/cmd link -d ratio:time</code>
Examples: 
<code>-d 0.7:10</code> (ratio & time)
<code>-d :30</code> (time only)
</blockquote>"""

zip_arg = """🗜️ <b>Zip Files</b>
<blockquote>
Create password-protected zips

<code>/cmd link -z password</code>
No password: <code>/cmd link -z</code>
</blockquote>"""

qual = """🎚️ <b>Quality Select</b>
<blockquote>
Manual quality selection with -s

<code>/cmd link -s</code>
Shows quality buttons for yt-dlp
</blockquote>"""

yt_opt = """⚙️ <b>YT-DLP Options</b>
<blockquote>
Advanced options with -opt

Format: <code>-opt key:value|key1:value1</code>
Supports complex formats: 
<code>wait_for_video:(5, 100)</code>
</blockquote>"""

convert_media = """🔄 <b>Media Conversion</b>
<blockquote>
Convert files with -ca/-cv

<code>/cmd link -ca mp3 -cv mp4</code>
Specific formats: 
<code>-ca mp3 + flac ogg</code>
</blockquote>"""

force_start = """▶️ <b>Force Start</b>
<blockquote>
Override queue settings

<code>/cmd link -f</code> (full force)
<code>/cmd link -fd</code> (force download)
<code>/cmd link -fu</code> (force upload)
</blockquote>"""

gdrive = """🗄️ <b>Google Drive</b>
<blockquote>
Special GDrive commands

<code>/cmd gdriveID -up gd</code>
Use prefixes: <code>tp:/sa:/mtp:</code>
</blockquote>"""

rclone_cl = """🔄 <b>RClone Config</b>
<blockquote>
Custom rclone operations

<code>/cmd rcl_path -up rc_path</code>
Use flags: <code>-rcf --buffer-size:8M</code>
</blockquote>"""

name_sub = """🔤 <b>Name Replacement</b>
<blockquote>
Modify filenames with -ns

Format: <code>-ns pattern/replacement</code>
Example: <code>-ns \[(.*)\]/\\1/s</code>
Supports regex patterns
</blockquote>"""

mixed_leech = """🌀 <b>Mixed Leech</b>
<blockquote>
Combine bot/user sessions

<code>/cmd link -ml</code>
Auto-switches based on file size
</blockquote>"""

thumbnail_layout = """🖼️ <b>Thumbnail Grid</b>
<blockquote>
Set collage layout with -tl

<code>/cmd link -tl 2x3</code>
Creates 2 rows x 3 columns
</blockquote>"""

leech_as = """📄 <b>Leech Format</b>
<blockquote>
Change leech type with -doc/-med

<code>/cmd link -doc</code> (as document)
<code>/cmd link -med</code> (as media)
</blockquote>"""

ffmpeg_cmds = """🎬 <b>FFmpeg Commands</b>
<blockquote>
Advanced media processing

Format: <code>-ff ["cmd1","cmd2"]</code>
Use variables: <code>mltb.*</code>
Add <code>-del</code> to remove originals
</blockquote>"""

YT_HELP_DICT = {
    "main": yt,
    "New-Name": new_name,
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
    "Mixed-Leech": mixed_leech,
    "Thumbnail-Layout": thumbnail_layout,
    "Leech-Type": leech_as,
    "FFmpeg-Cmds": ffmpeg_cmds,
}

MIRROR_HELP_DICT = {
    "main": mirror,
    "New-Name": new_name,
    "DL-Auth": """🔑 <b>Auth Settings</b>
    <blockquote>
    <code>-au username -ap password</code>
    For password-protected links
    </blockquote>""",
    "Headers": """📋 <b>Custom Headers</b>
    <blockquote>
    Add headers with -h
    <code>-h key:value key1:value1</code>
    </blockquote>""",
    "Extract/Zip": extract_zip,
    "Select-Files": """📑 <b>File Selection</b>
    <blockquote>
    Select torrent files with -s
    Reply to torrent: <code>/cmd -s</code>
    </blockquote>""",
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
    "Mixed-Leech": mixed_leech,
    "Thumbnail-Layout": thumbnail_layout,
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

RSS_HELP_MESSAGE = """📰 <b>RSS Management</b>
<blockquote>
Format: <code>Title URL -c cmd -inf filters</code>
Example: <code>Example https://example.com/rss -c /cmd -inf 1080</code>

Filters: <code>-inf "1080|hevc" -exf "web|low"</code>
Time format: <code>-d ratio:minutes</code>
</blockquote>"""

PASSWORD_ERROR_MESSAGE = """🔒 <b>Password Required</b>
<blockquote>
Format: <code>link::password</code>
Example: <code>https://example.com::secret123</code>
</blockquote>"""

help_string = f"""
🎯 <b>Basic Commands</b>
<blockquote>
<code>/{BotCommands.MirrorCommand[0]}</code> - Upload to Cloud
<code>/{BotCommands.LeechCommand[0]}</code> - Upload to Telegram
<code>/{BotCommands.YtdlCommand[0]}</code> - YT-DLP Mirror
<code>/{BotCommands.CloneCommand}</code> - Copy GDrive Content
<code>/{BotCommands.StatusCommand}</code> - Show Active Tasks
</blockquote>

⚙️ <b>Configuration Commands</b>
<blockquote>
<code>/{BotCommands.UserSetCommand[0]}</code> - User Settings
<code>/{BotCommands.BotSetCommand[0]}</code> - Bot Settings
<code>/{BotCommands.LogCommand}</code> - Get Logs
<code>/{BotCommands.StatsCommand}</code> - System Stats
</blockquote>

🔧 <b>Advanced Controls</b>
<blockquote>
<code>/{BotCommands.ForceStartCommand[0]}</code> - Force Start
<code>/{BotCommands.CancelAllCommand}</code> - Cancel All
<code>/{BotCommands.ListCommand}</code> - Drive Search
<code>/{BotCommands.SearchCommand}</code> - Torrent Search
</blockquote>

📚 <b>Full documentation available in</b> <a href='https://github.com/yt-dlp/yt-dlp'>GitHub Repo</a>
"""
