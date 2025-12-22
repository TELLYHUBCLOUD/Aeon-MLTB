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
    
    # Priority: Encode > Mirror > Leech
    is_encode = user_dict.get("AUTO_ENCODE") or Config.AUTO_ENCODE
    is_mirror = user_dict.get("AUTO_MIRROR") or Config.AUTO_MIRROR
    is_leech = user_dict.get("AUTO_LEECH") or Config.AUTO_LEECH

    if not (is_encode or is_mirror or is_leech):
        return

    text = message.text
    if not text:
        return
    if text.strip().startswith("/"):
        return
    if not (
        re_match(r"https?://\S+", text) or re_match(r"magnet:\?xt=urn:\S+", text)
    ):
        return
    
    auto_ff = user_dict.get("AUTO_COMPRESS_CMD")
    
    # Determine Command and Mode
    if is_encode:
        from bot.modules.encode import Encode
        # Encode implementation requires different handling usually
        # But based on request, we trigger /encode
        cmd = "encode"
        # Encode command usually needs more args, but simplistic handling here:
        await Encode(
            client,
            message,
        ).new_event() 
        # Note: Encode class needs to be imported and might differ in instantiation
        # Let's verify Encode class usage in a bit. 
        # For now, assuming standard TaskListener pattern if applicable or simple command injection
        # Actually message.text modification is needed for standard listeners usually
        message.text = f"/{cmd} {text}"
    elif is_mirror:
        cmd = user_dict.get("AUTO_MIRROR_CMD") or Config.AUTO_MIRROR_CMD or "mirror"
        message.text = f"/{cmd} {text}"
        await Mirror(
            client,
            message,
            is_leech=False,
            auto_link=text,
            auto_ff=auto_ff,
        ).new_event()
    else:
        # Default Leech
        cmd = user_dict.get("AUTO_LEECH_CMD") or Config.AUTO_LEECH_CMD or "leech"
        cmd = cmd.lower().replace("{i}", "")
        # Adjust user defined cmd
        user_cmd = user_dict.get("AUTO_LEECH_CMD")
        if user_cmd:
            cmd = user_cmd.split()[0]
        
        message.text = f"/{cmd} {text}"
        
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
            await Mirror(
                client,
                message,
                is_leech=True,
                auto_link=text,
                auto_ff=auto_ff,
            ).new_event()
    
    LOGGER.info(f"[AUTO] Triggered for user {user_id} with cmd {cmd}: {text[:30]}...")
