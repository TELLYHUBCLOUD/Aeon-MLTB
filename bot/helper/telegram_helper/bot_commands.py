from bot.core.config_manager import Config


def get_command(cmd):
    """Get command with suffix if configured"""
    suffix = getattr(Config, "CMD_SUFFIX", "") or ""
    return f"{cmd}{suffix}"


class BotCommands:
    @classmethod
    def get_commands(cls):
        """Get all commands with current suffix"""
        suffix = getattr(Config, "CMD_SUFFIX", "") or ""
        return {
            "StartCommand": "start",
            "MirrorCommand": [f"mirror{suffix}", f"m{suffix}"],
            "JdMirrorCommand": [f"jdmirror{suffix}", f"jm{suffix}"],
            "NzbMirrorCommand": [f"nzbmirror{suffix}", f"nm{suffix}"],
            "YtdlCommand": [f"ytdl{suffix}", f"y{suffix}"],
            "LeechCommand": [f"leech{suffix}", f"l{suffix}"],
            "JdLeechCommand": [f"jdleech{suffix}", f"jl{suffix}"],
            "NzbLeechCommand": [f"nzbleech{suffix}", f"nl{suffix}"],
            "YtdlLeechCommand": [f"ytdlleech{suffix}", f"yl{suffix}"],
            "CloneCommand": f"clone{suffix}",
            "MediaInfoCommand": f"mediainfo{suffix}",
            "CountCommand": f"count{suffix}",
            "DeleteCommand": f"del{suffix}",
            "CancelAllCommand": f"cancelall{suffix}",
            "ForceStartCommand": [f"forcestart{suffix}", f"fs{suffix}"],
            "ListCommand": f"list{suffix}",
            "SearchCommand": f"search{suffix}",
            "HydraSearchCommand": f"nzbsearch{suffix}",
            "StatusCommand": [f"status{suffix}", "statusall", "sall"],
            "UsersCommand": f"users{suffix}",
            "AuthorizeCommand": f"auth{suffix}",
            "UnAuthorizeCommand": f"unauth{suffix}",
            "AddSudoCommand": f"addsudo{suffix}",
            "RmSudoCommand": f"rmsudo{suffix}",
            "PingCommand": f"ping{suffix}",
            "RestartCommand": [f"restart{suffix}", "restartall"],
            "StatsCommand": f"stats{suffix}",
            "HelpCommand": f"help{suffix}",
            "LogCommand": f"log{suffix}",
            "ShellCommand": f"shell{suffix}",
            "AExecCommand": f"aexec{suffix}",
            "ExecCommand": f"exec{suffix}",
            "ClearLocalsCommand": f"clearlocals{suffix}",
            "BotSetCommand": f"botsettings{suffix}",
            "UserSetCommand": f"settings{suffix}",
            "SpeedTest": f"speedtest{suffix}",
            "BroadcastCommand": [f"broadcast{suffix}", "broadcastall"],
            "SelectCommand": f"sel{suffix}",
            "RssCommand": f"rss{suffix}",
            "SoxCommand": [f"spectrum{suffix}", f"sox{suffix}"],
        }

    # Static properties for backward compatibility - using class methods
    @classmethod
    @property
    def StartCommand(cls):
        return cls.get_commands()["StartCommand"]

    @classmethod
    @property
    def MirrorCommand(cls):
        return cls.get_commands()["MirrorCommand"]

    @classmethod
    @property
    def JdMirrorCommand(cls):
        return cls.get_commands()["JdMirrorCommand"]

    @classmethod
    @property
    def NzbMirrorCommand(cls):
        return cls.get_commands()["NzbMirrorCommand"]

    @classmethod
    @property
    def YtdlCommand(cls):
        return cls.get_commands()["YtdlCommand"]

    @classmethod
    @property
    def LeechCommand(cls):
        return cls.get_commands()["LeechCommand"]

    @classmethod
    @property
    def JdLeechCommand(cls):
        return cls.get_commands()["JdLeechCommand"]

    @classmethod
    @property
    def NzbLeechCommand(cls):
        return cls.get_commands()["NzbLeechCommand"]

    @classmethod
    @property
    def YtdlLeechCommand(cls):
        return cls.get_commands()["YtdlLeechCommand"]

    @classmethod
    @property
    def CloneCommand(cls):
        return cls.get_commands()["CloneCommand"]

    @classmethod
    @property
    def MediaInfoCommand(cls):
        return cls.get_commands()["MediaInfoCommand"]

    @classmethod
    @property
    def CountCommand(cls):
        return cls.get_commands()["CountCommand"]

    @classmethod
    @property
    def DeleteCommand(cls):
        return cls.get_commands()["DeleteCommand"]

    @classmethod
    @property
    def CancelAllCommand(cls):
        return cls.get_commands()["CancelAllCommand"]

    @classmethod
    @property
    def ForceStartCommand(cls):
        return cls.get_commands()["ForceStartCommand"]

    @classmethod
    @property
    def ListCommand(cls):
        return cls.get_commands()["ListCommand"]

    @classmethod
    @property
    def SearchCommand(cls):
        return cls.get_commands()["SearchCommand"]

    @classmethod
    @property
    def HydraSearchCommand(cls):
        return cls.get_commands()["HydraSearchCommand"]

    @classmethod
    @property
    def StatusCommand(cls):
        return cls.get_commands()["StatusCommand"]

    @classmethod
    @property
    def UsersCommand(cls):
        return cls.get_commands()["UsersCommand"]

    @classmethod
    @property
    def AuthorizeCommand(cls):
        return cls.get_commands()["AuthorizeCommand"]

    @classmethod
    @property
    def UnAuthorizeCommand(cls):
        return cls.get_commands()["UnAuthorizeCommand"]

    @classmethod
    @property
    def AddSudoCommand(cls):
        return cls.get_commands()["AddSudoCommand"]

    @classmethod
    @property
    def RmSudoCommand(cls):
        return cls.get_commands()["RmSudoCommand"]

    @classmethod
    @property
    def PingCommand(cls):
        return cls.get_commands()["PingCommand"]

    @classmethod
    @property
    def RestartCommand(cls):
        return cls.get_commands()["RestartCommand"]

    @classmethod
    @property
    def StatsCommand(cls):
        return cls.get_commands()["StatsCommand"]

    @classmethod
    @property
    def HelpCommand(cls):
        return cls.get_commands()["HelpCommand"]

    @classmethod
    @property
    def LogCommand(cls):
        return cls.get_commands()["LogCommand"]

    @classmethod
    @property
    def ShellCommand(cls):
        return cls.get_commands()["ShellCommand"]

    @classmethod
    @property
    def AExecCommand(cls):
        return cls.get_commands()["AExecCommand"]

    @classmethod
    @property
    def ExecCommand(cls):
        return cls.get_commands()["ExecCommand"]

    @classmethod
    @property
    def ClearLocalsCommand(cls):
        return cls.get_commands()["ClearLocalsCommand"]

    @classmethod
    @property
    def BotSetCommand(cls):
        return cls.get_commands()["BotSetCommand"]

    @classmethod
    @property
    def UserSetCommand(cls):
        return cls.get_commands()["UserSetCommand"]

    @classmethod
    @property
    def SpeedTest(cls):
        return cls.get_commands()["SpeedTest"]

    @classmethod
    @property
    def BroadcastCommand(cls):
        return cls.get_commands()["BroadcastCommand"]

    @classmethod
    @property
    def SelectCommand(cls):
        return cls.get_commands()["SelectCommand"]

    @classmethod
    @property
    def RssCommand(cls):
        return cls.get_commands()["RssCommand"]

    @classmethod
    @property
    def SoxCommand(cls):
        return cls.get_commands()["SoxCommand"]
