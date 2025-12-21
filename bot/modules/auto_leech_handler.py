from re import match as re_match
from bot import LOGGER, user_data
from bot.core.config_manager import Config
from bot.helper.ext_utils.bot_utils import new_task
from bot.modules.clone import Clone
from bot.modules.mirror_leech import Mirror

@new_task
async def auto_leech_handler(client, message):
    user_id = message.from_user.id
    user_dict = user_data.get(user_id, {})
    if not user_dict.get("AUTO_LEECH"):
        return
    text = message.text
    if not text:
        return
    if text.startswith("/"):
        return
    if not (
        re_match(r"https?://\S+", text) or re_match(r"magnet:\?xt=urn:\S+", text)
    ):
        return
    auto_ff = user_dict.get("AUTO_COMPRESS_CMD")
    cmd = user_dict.get("AUTO_LEECH_CMD") or Config.AUTO_LEECH_CMD or "leech"
    cmd = cmd.lower().replace("{i}", "") # Handle placeholder if present in simple check
    
    # Simple check, usually cmd is just "leech" or "mirror"
    # But user might set "leech -z" etc.
    # We will let Mirror parse arguments if we construct the message correctly?
    # Or just use "leech" / "mirror" explicitly ?
    
    # Previous implementation used Config.AUTO_LEECH_CMD. 
    # Let's respect usage in Mirror call.
    
    # Re-implementing based on previous file content logic:
    
    # cmd comes from Config in original file.
    cmd = Config.AUTO_LEECH_CMD.lower() if Config.AUTO_LEECH_CMD else "leech"
    
    # But user settings has AUTO_LEECH_CMD. 
    user_cmd = user_dict.get("AUTO_LEECH_CMD")
    if user_cmd:
        # If user defined cmd, use it. But we need to extract the base command.
        cmd = user_cmd.split()[0]
    
    message.text = f"/{cmd} {text}"
    LOGGER.info(f"[AUTO_LEECH] Triggered for user {user_id} with cmd {cmd}: {text[:30]}...")

    if cmd == "clone":
        await Clone(
            client,
            message,
        ).new_event()
    elif cmd == "mirror":
        await Mirror(
            client,
            message,
            is_leech=False,
            auto_link=text,
            auto_ff=auto_ff,
        ).new_event()
    else:
        # Default to leech
        await Mirror(
            client,
            message,
            is_leech=True,
            auto_link=text,
            auto_ff=auto_ff,
        ).new_event()
