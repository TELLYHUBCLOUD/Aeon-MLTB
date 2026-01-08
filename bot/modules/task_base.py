from bot.helper.listeners.task_listener import TaskListener
from bot.helper.ext_utils.bot_utils import arg_parser, is_flag_enabled
from bot.core.config_manager import Config
from bot.helper.telegram_helper.message_utils import send_message

class TaskBase(TaskListener):
    def __init__(self, client, message, **kwargs):
        self.message = message
        self.client = client
        super().__init__()
        self.args = {}
        # Properly process kwargs
        self.bulk = kwargs.get("bulk", [])
        self.multi_tag = kwargs.get("multi_tag", "")
        self.options = kwargs.get("options", "")
        self.same_dir = kwargs.get("same_dir", {})
        self.link = ""
        self.multi = 0

    def get_default_args(self):
        """Returns the default argument dictionary for the task."""
        return {
            "-doc": False,
            "-med": False,
            "-d": False,
            "-j": False,
            "-s": False,
            "-b": False,
            "-e": False,
            "-z": False,
            "-sv": False,
            "-ss": False,
            "-f": False,
            "-fd": False,
            "-fu": False,
            "-hl": False,
            "-bt": False,
            "-ut": False,
            "-mt": False,
            "-merge-video": False,
            "-merge-audio": False,
            "-merge-subtitle": False,
            "-merge-all": False,
            "-merge-image": False,
            "-merge-pdf": False,
            "-i": 0,
            "-sp": 0,
            "link": "",
            "-n": "",
            "-m": "",  # Same directory operation flag
            "-watermark": "",
            "-iwm": "",
            "-up": "",
            "-rcf": "",
            "-au": "",
            "-ap": "",
            "-h": [],
            "-t": "",
            "-ca": "",
            "-cv": "",
            "-ns": "",
            "-md": "",
            "-metadata-title": "",
            "-metadata-author": "",
            "-metadata-comment": "",
            "-metadata-all": "",
            "-metadata-video-title": "",
            "-metadata-video-author": "",
            "-metadata-video-comment": "",
            "-metadata-audio-title": "",
            "-metadata-audio-author": "",
            "-metadata-audio-comment": "",
            "-metadata-subtitle-title": "",
            "-metadata-subtitle-author": "",
            "-metadata-subtitle-comment": "",
            "-tl": "",
            "-ff": set(),
            "-compress": False,
            "-comp-video": False,
            "-comp-audio": False,
            "-comp-image": False,
            "-comp-document": False,
            "-comp-subtitle": False,
            "-comp-archive": False,
            "-video-fast": False,
            "-video-medium": False,
            "-video-slow": False,
            "-audio-fast": False,
            "-audio-medium": False,
            "-audio-slow": False,
            "-image-fast": False,
            "-image-medium": False,
            "-image-slow": False,
            "-document-fast": False,
            "-document-medium": False,
            "-document-slow": False,
            "-subtitle-fast": False,
            "-subtitle-medium": False,
            "-subtitle-slow": False,
            "-archive-fast": False,
            "-archive-medium": False,
            "-archive-slow": False,
            "-trim": "",
            "-extract": False,
            "-extract-video": False,
            "-extract-audio": False,
            "-extract-subtitle": False,
            "-extract-attachment": False,
            "-extract-video-index": "",
            "-extract-audio-index": "",
            "-extract-subtitle-index": "",
            "-extract-attachment-index": "",
            "-extract-video-codec": "",
            "-extract-audio-codec": "",
            "-extract-subtitle-codec": "",
            "-extract-maintain-quality": "",
            "-extract-priority": "",
            "-remove": False,
            "-remove-video": False,
            "-remove-audio": False,
            "-remove-subtitle": False,
            "-remove-attachment": False,
            "-remove-metadata": False,
            "-remove-video-index": "",
            "-remove-audio-index": "",
            "-remove-subtitle-index": "",
            "-remove-attachment-index": "",
            "-remove-priority": "",
            "-add": False,
            "-add-video": False,
            "-add-audio": False,
            "-add-subtitle": False,
            "-add-attachment": False,
            "-del": "",
            "-preserve": False,
            "-replace": False,
            # Shorter index flags
            "-vi": "",
            "-ai": "",
            "-si": "",
            "-ati": "",
            # Remove shorter index flags
            "-rvi": "",
            "-rai": "",
            "-rsi": "",
            "-rati": "",
            # Swap flags
            "-swap": False,
            "-swap-audio": False,
            "-swap-video": False,
            "-swap-subtitle": False,
            "-lulu": False,
            "-buz": False,
            "-pix": False,
            "-sync": False, # Clone specific
            "-q": "", # Encode specific
            "-an": False, # Encode specific
            "-sn": False, # Encode specific
        }

    async def parse_args(self):
        """Parses arguments from the message."""
        if (
            not self.message
            or not hasattr(self.message, "text")
            or self.message.text is None
        ):
            return False

        text = self.message.text.split("\n")
        input_list = text[0].split(" ")
        self.args = self.get_default_args()
        arg_parser(input_list[1:], self.args)

        # Check if flags are enabled
        for flag in list(self.args.keys()):
            if flag.startswith("-") and not is_flag_enabled(flag):
                if isinstance(self.args[flag], bool):
                    self.args[flag] = False
                elif isinstance(self.args[flag], set):
                    self.args[flag] = set()
                elif isinstance(self.args[flag], str):
                    self.args[flag] = ""
                elif isinstance(self.args[flag], int):
                    self.args[flag] = 0

        # Common attributes mapping
        self.link = self.args["link"]
        self.name = self.args["-n"]
        self.up_dest = self.args["-up"]
        self.rc_flags = self.args["-rcf"]
        self.multi = int(self.args["-i"])
        self.is_bulk = self.args["-b"]

        return input_list

    async def init_bulk(self, input_list, bulk_start, bulk_end, listener_class, **kwargs):
        """Initializes bulk tasks."""
        try:
            if not self.bulk:
                from bot.helper.ext_utils.bulk_links import extract_bulk_links
                self.bulk = await extract_bulk_links(self.message, bulk_start, bulk_end)

            if len(self.bulk) == 0:
                return

            b_msg = input_list[:1]
            self.options = " ".join(input_list[1:])
            b_msg.append(f"{self.bulk[0]} -i {len(self.bulk)} {self.options}")

            # This part sends a new message for the first link with bulk info
            nextmsg = await send_message(self.message, " ".join(b_msg))
            nextmsg = await self.client.get_messages(chat_id=self.message.chat.id, message_ids=nextmsg.id)
            if self.message.from_user:
                nextmsg.from_user = self.user
            else:
                nextmsg.sender_chat = self.user

            # Start the listener for the first item
            await listener_class(
                self.client,
                nextmsg,
                bulk=self.bulk,
                multi_tag=self.multi_tag,
                options=self.options,
                **kwargs
            ).new_event()

            from bot.helper.telegram_helper.message_utils import delete_links
            await delete_links(self.message)

        except Exception as e:
            from bot import LOGGER
            LOGGER.error(f"Bulk init error: {e}")
