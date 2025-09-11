# ruff: noqa: F405
from pyrogram.filters import command, regex
from pyrogram.handlers import (
    CallbackQueryHandler,
    EditedMessageHandler,
    MessageHandler,
)

from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.modules import (
    add_sudo,
    aeon_callback,
    aioexecute,
    arg_usage,
    authorize,
    bot_help,
    bot_stats,
    broadcast,
    cancel,
    cancel_all_buttons,
    cancel_all_update,
    cancel_multi,
    clear,
    clone_node,
    confirm_restart,
    confirm_selection,
    count_node,
    delete_file,
    edit_bot_settings,
    edit_user_settings,
    execute,
    gdrive_search,
    get_rss_menu,
    get_users_settings,
    hydra_search,
    jd_leech,
    jd_mirror,
    leech,
    log,
    mediainfo,
    mirror,
    nzb_leech,
    nzb_mirror,
    ping,
    remove_from_queue,
    remove_sudo,
    restart_bot,
    rss_listener,
    run_shell,
    select,
    select_type,
    send_bot_settings,
    send_user_settings,
    spectrum_handler,
    speedtest,
    start,
    status_pages,
    task_status,
    torrent_search,
    torrent_search_update,
    unauthorize,
    ytdl,
    ytdl_leech,
)

from .aeon_client import TgClient


def add_handlers():
    # Get current commands with suffix
    commands = BotCommands.get_commands()
    
    command_filters = {
        "authorize": (
            authorize,
            commands['AuthorizeCommand'],
            CustomFilters.sudo,
        ),
        "unauthorize": (
            unauthorize,
            commands['UnAuthorizeCommand'],
            CustomFilters.sudo,
        ),
        "add_sudo": (
            add_sudo,
            commands['AddSudoCommand'],
            CustomFilters.sudo,
        ),
        "remove_sudo": (
            remove_sudo,
            commands['RmSudoCommand'],
            CustomFilters.sudo,
        ),
        "send_bot_settings": (
            send_bot_settings,
            commands['BotSetCommand'],
            CustomFilters.sudo,
        ),
        "cancel_all_buttons": (
            cancel_all_buttons,
            commands['CancelAllCommand'],
            CustomFilters.authorized,
        ),
        "clone_node": (
            clone_node,
            commands['CloneCommand'],
            CustomFilters.authorized,
        ),
        "aioexecute": (
            aioexecute,
            commands['AExecCommand'],
            CustomFilters.sudo,
        ),
        "execute": (
            execute,
            commands['ExecCommand'],
            CustomFilters.sudo,
        ),
        "clear": (
            clear,
            commands['ClearLocalsCommand'],
            CustomFilters.sudo,
        ),
        "select": (
            select,
            commands['SelectCommand'],
            CustomFilters.authorized,
        ),
        "remove_from_queue": (
            remove_from_queue,
            commands['ForceStartCommand'],
            CustomFilters.authorized,
        ),
        "count_node": (
            count_node,
            commands['CountCommand'],
            CustomFilters.authorized,
        ),
        "delete_file": (
            delete_file,
            commands['DeleteCommand'],
            CustomFilters.authorized,
        ),
        "gdrive_search": (
            gdrive_search,
            commands['ListCommand'],
            CustomFilters.authorized,
        ),
        "mirror": (
            mirror,
            commands['MirrorCommand'],
            CustomFilters.authorized,
        ),
        "jd_mirror": (
            jd_mirror,
            commands['JdMirrorCommand'],
            CustomFilters.authorized,
        ),
        "leech": (
            leech,
            commands['LeechCommand'],
            CustomFilters.authorized,
        ),
        "jd_leech": (
            jd_leech,
            commands['JdLeechCommand'],
            CustomFilters.authorized,
        ),
        "get_rss_menu": (
            get_rss_menu,
            commands['RssCommand'],
            CustomFilters.authorized,
        ),
        "run_shell": (
            run_shell,
            commands['ShellCommand'],
            CustomFilters.owner,
        ),
        "start": (
            start,
            commands['StartCommand'],
            None,
        ),
        "log": (
            log,
            commands['LogCommand'],
            CustomFilters.sudo,
        ),
        "restart_bot": (
            restart_bot,
            commands['RestartCommand'],
            CustomFilters.sudo,
        ),
        "ping": (
            ping,
            commands['PingCommand'],
            CustomFilters.authorized,
        ),
        "bot_help": (
            bot_help,
            commands['HelpCommand'],
            CustomFilters.authorized,
        ),
        "bot_stats": (
            bot_stats,
            commands['StatsCommand'],
            CustomFilters.authorized,
        ),
        "task_status": (
            task_status,
            commands['StatusCommand'],
            CustomFilters.authorized,
        ),
        "torrent_search": (
            torrent_search,
            commands['SearchCommand'],
            CustomFilters.authorized,
        ),
        "get_users_settings": (
            get_users_settings,
            commands['UsersCommand'],
            CustomFilters.sudo,
        ),
        "send_user_settings": (
            send_user_settings,
            commands['UserSetCommand'],
            CustomFilters.authorized,
        ),
        "ytdl": (
            ytdl,
            commands['YtdlCommand'],
            CustomFilters.authorized,
        ),
        "ytdl_leech": (
            ytdl_leech,
            commands['YtdlLeechCommand'],
            CustomFilters.authorized,
        ),
        "mediainfo": (
            mediainfo,
            commands['MediaInfoCommand'],
            CustomFilters.authorized,
        ),
        "speedtest": (
            speedtest,
            commands['SpeedTest'],
            CustomFilters.authorized,
        ),
        "broadcast": (
            broadcast,
            commands['BroadcastCommand'],
            CustomFilters.owner,
        ),
        "nzb_mirror": (
            nzb_mirror,
            commands['NzbMirrorCommand'],
            CustomFilters.authorized,
        ),
        "nzb_leech": (
            nzb_leech,
            commands['NzbLeechCommand'],
            CustomFilters.authorized,
        ),
        "hydra_search": (
            hydra_search,
            commands['HydraSearchCommand'],
            CustomFilters.authorized,
        ),
        "spectrum_handler": (
            spectrum_handler,
            commands['SoxCommand'],
            CustomFilters.authorized,
        ),
    }

    for handler_func, command_name, custom_filter in command_filters.values():
        if custom_filter:
            filters_to_apply = (
                command(command_name, case_sensitive=True) & custom_filter
            )
        else:
            filters_to_apply = command(command_name, case_sensitive=True)

        TgClient.bot.add_handler(
            MessageHandler(
                handler_func,
                filters=filters_to_apply,
            ),
        )

    regex_filters = {
        "^botset": edit_bot_settings,
        "^canall": cancel_all_update,
        "^stopm": cancel_multi,
        "^sel": confirm_selection,
        "^list_types": select_type,
        "^rss": rss_listener,
        "^torser": torrent_search_update,
        "^userset": edit_user_settings,
        "^help": arg_usage,
        "^status": status_pages,
        "^botrestart": confirm_restart,
        "^aeon": aeon_callback,
    }

    for regex_filter, handler_func in regex_filters.items():
        TgClient.bot.add_handler(
            CallbackQueryHandler(handler_func, filters=regex(regex_filter)),
        )

    TgClient.bot.add_handler(
        EditedMessageHandler(
            run_shell,
            filters=command(commands['ShellCommand'], case_sensitive=True)
            & CustomFilters.owner,
        ),
    )
    TgClient.bot.add_handler(
        MessageHandler(
            cancel,
            filters=regex(r"^/stop(_\w+)?(?!all)") & CustomFilters.authorized,
        ),
    )
