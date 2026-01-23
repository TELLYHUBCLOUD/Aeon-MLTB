# ruff: noqa: RUF012
from bot.core.config_manager import Config

i = Config.CMD_SUFFIX


class BotCommands:
    StartCommand = "start"
    MirrorCommand = [f"mirror{i}", f"m{i}"]
    JdMirrorCommand = [f"jdmirror{i}", f"jm{i}"]
    NzbMirrorCommand = [f"nzbmirror{i}", f"nm{i}"]
    YtdlCommand = [f"ytdl{i}", f"y{i}"]

    LeechCommand = [f"leech{i}", f"l{i}"]
    JdLeechCommand = [f"jdleech{i}", f"jl{i}"]
    NzbLeechCommand = [f"nzbleech{i}", f"nl{i}"]
    YtdlLeechCommand = [f"ytdlleech{i}", f"yl{i}"]
    
    CloneCommand = f"clone{i}"
    EncodeCommand = f"encode{i}"
    MergeCommand = f"merge{i}"
    MergeAudioCommand = f"mergeaudio{i}"
    TeraboxCommand = [f"terabox{i}", f"tb{i}"]
    MdoneCommand = f"mdone{i}"
    CancelTaskCommand = [f"cancel{i}", f"c{i}"]

    MediaInfoCommand = f"mediainfo{i}"
    CountCommand = f"count{i}"
    DeleteCommand = f"del{i}"
    CancelAllCommand = f"cancelall{i}"
    ForceStartCommand = [f"forcestart{i}", f"fs{i}"]
    ListCommand = f"list{i}"
    SearchCommand = f"search{i}"
    HydraSearchCommand = f"nzbsearch{i}"
    StatusCommand = [f"status{i}", "statusall", "sall"]
    UsersCommand = f"users{i}"
    AuthorizeCommand = [f"auth{i}", "a"]
    UnAuthorizeCommand = [f"unauth{i}", "ua"]
    AddSudoCommand = [f"addsudo{i}", "as"]
    RmSudoCommand = [f"rmsudo{i}", "rs"]
    PingCommand = [f"ping{i}", "pong{i}", "pong"]
    RestartCommand = [f"restart{i}", "restartall"]
    StatsCommand = [f"stats{i}", "st"]
    HelpCommand = [f"help{i}", "h"]
    LogCommand = [f"log{i}", "l"]
    ShellCommand = f"shell{i}"
    AExecCommand = f"aexec{i}"
    ExecCommand = f"exec{i}"
    ClearLocalsCommand = f"clearlocals{i}"
    BotSetCommand = [f"botsettings{i}", "bs"]
    UserSetCommand = [f"settings{i}", "us"]
    SetCommand = [f"set{i}", "thum"]
    SpeedTest = f"speedtest{i}"
    BroadcastCommand = [f"broadcast{i}", "broadcastall"]
    SelectCommand = f"sel{i}"
    RssCommand = f"rss{i}"
    SoxCommand = [f"spectrum{i}", f"sox{i}"]
