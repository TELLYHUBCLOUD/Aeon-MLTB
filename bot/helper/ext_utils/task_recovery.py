from asyncio import create_task, sleep
from logging import getLogger
from time import time

from bot import LOGGER
from bot.core.config_manager import Config
from bot.helper.ext_utils.db_handler import database
from bot.helper.ext_utils.links_utils import (
    is_gdrive_link,
    is_magnet,
    is_rclone_path,
    is_telegram_link,
    is_url,
)
from bot.helper.telegram_helper.message_utils import send_message
from bot.modules.mirror_leech import Mirror
from bot.modules.ytdlp import YtDlp

LOGGER = getLogger(__name__)


class TaskRecovery:
    """Handles automatic recovery and restart of incomplete tasks after bot restart."""

    def __init__(self):
        self.recovery_in_progress = False

    async def recover_incomplete_tasks(self):
        """Recovers and restarts incomplete tasks from database after bot restart."""
        if (
            not Config.DATABASE_URL
            or not Config.AUTO_RESTART_TASKS
            or self.recovery_in_progress
        ):
            return

        self.recovery_in_progress = True
        LOGGER.info("Starting task recovery process...")

        try:
            incomplete_tasks = await database.get_incomplete_tasks_detailed()
            if not incomplete_tasks:
                LOGGER.info("No incomplete tasks found for recovery")
                return

            recovered_count = 0
            failed_count = 0

            for task_data in incomplete_tasks:
                try:
                    if await self._restart_task(task_data):
                        recovered_count += 1
                        await sleep(2)  # Prevent overwhelming the system
                    else:
                        failed_count += 1
                except Exception as e:
                    LOGGER.error(
                        f"Failed to recover task {task_data.get('link', 'unknown')}: {e}"
                    )
                    failed_count += 1

            LOGGER.info(
                f"Task recovery completed. Recovered: {recovered_count}, Failed: {failed_count}"
            )

            # Send summary to owner if there were recoveries
            if recovered_count > 0 or failed_count > 0:
                summary_msg = "🔄 <b>Task Recovery Summary</b>\n\n"
                summary_msg += f"✅ <b>Recovered:</b> {recovered_count}\n"
                summary_msg += f"❌ <b>Failed:</b> {failed_count}\n"
                summary_msg += f"📊 <b>Total:</b> {recovered_count + failed_count}"

                try:
                    await send_message(Config.OWNER_ID, summary_msg)
                except Exception as e:
                    LOGGER.error(f"Failed to send recovery summary: {e}")

        except Exception as e:
            LOGGER.error(f"Error during task recovery: {e}")
        finally:
            self.recovery_in_progress = False

    async def _restart_task(self, task_data):
        """Attempts to restart a single task based on stored data."""
        try:
            link = task_data.get("link")
            chat_id = task_data.get("chat_id")
            user_id = task_data.get("user_id")
            task_type = task_data.get("task_type", "mirror")
            options = task_data.get("options", {})

            if not all([link, chat_id, user_id]):
                LOGGER.warning(f"Incomplete task data: {task_data}")
                return False

            # Validate link is still accessible
            if not await self._validate_link(link):
                LOGGER.warning(f"Link no longer accessible: {link}")
                return False

            # Create a mock message object for task restart
            mock_message = await self._create_mock_message(
                chat_id, user_id, link, options
            )

            if not mock_message:
                return False

            # Restart the appropriate task type
            if task_type == "ytdl":
                create_task(YtDlp(None, mock_message, **options).new_event())
            else:
                create_task(Mirror(None, mock_message, **options).new_event())

            LOGGER.info(f"Successfully restarted task: {link}")
            return True

        except Exception as e:
            LOGGER.error(
                f"Failed to restart task {task_data.get('link', 'unknown')}: {e}"
            )
            return False

    async def _validate_link(self, link):
        """Validates if a link is still accessible for download."""
        try:
            if is_telegram_link(link):
                return True  # Telegram links are generally persistent
            if is_magnet(link):
                return True  # Magnet links don't expire
            if is_gdrive_link(link):
                return True  # Will be validated during actual download
            if is_rclone_path(link):
                return True  # Rclone paths are persistent
            if is_url(link):
                # For HTTP links, we could do a HEAD request but it might be expensive
                # For now, assume they're still valid
                return True
            return True
        except Exception:
            return False

    async def _create_mock_message(self, chat_id, user_id, link, options):
        """Creates a mock message object for task restart."""
        try:
            from types import SimpleNamespace

            # Create mock user
            mock_user = SimpleNamespace()
            mock_user.id = user_id
            mock_user.username = None
            mock_user.mention = f"User {user_id}"

            # Create mock chat
            mock_chat = SimpleNamespace()
            mock_chat.id = chat_id
            mock_chat.type = SimpleNamespace()
            mock_chat.type.PRIVATE = "private"
            mock_chat.type.name = "SUPERGROUP"

            # Create mock message
            mock_message = SimpleNamespace()
            mock_message.id = int(time() * 1000)  # Unique message ID
            mock_message.chat = mock_chat
            mock_message.from_user = mock_user
            mock_message.sender_chat = None
            mock_message.reply_to_message = None
            mock_message.reply_to_message_id = None
            mock_message.message_thread_id = None
            mock_message.topic_message = False
            mock_message.link = f"https://t.me/c/{abs(chat_id)}/{mock_message.id}"

            # Construct command text with options
            cmd_text = f"/mirror {link}"
            if options:
                for key, value in options.items():
                    if value and key.startswith("-"):
                        cmd_text += f" {key}"
                        if not value:
                            cmd_text += f" {value}"

            mock_message.text = cmd_text
            mock_message.command = cmd_text.split()

            return mock_message

        except Exception as e:
            LOGGER.error(f"Failed to create mock message: {e}")
            return None


# Global task recovery instance
task_recovery = TaskRecovery()
