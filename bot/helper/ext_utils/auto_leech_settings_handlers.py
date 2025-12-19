"""Auto Leech validation and handler functions for users_settings.py

Add these functions at the END of users_settings.py file (around line 5014)
"""


async def set_auto_leech_cmd(client, message, pre_message, user_id):
    """Handle auto leech command template input with validation"""
    from bot import LOGGER, database
    from bot.helper.ext_utils.db_handler import update_user_ldata
    from bot.helper.telegram_helper.message_utils import delete_message, send_message
    from html import escape
    
    try:
        cmd_template = message.text.strip()
        
        # Validation: Must contain {i} placeholder
        if "{i}" not in cmd_template:
            await send_message(
                message,
                "❌ <b>Invalid Template</b>\n\n"
                "Command template must contain <code>{i}</code> placeholder!\n\n"
                "<b>Examples:</b>\n"
                "• <code>leech {i}</code>\n"
                "• <code>leech {i} -s</code>\n"
                "• <code>leech {i} -z password123</code>"
            )
            return
        
        # Update user data
        update_user_ldata(user_id, "auto_leech_cmd", cmd_template)
        await database.update_user_data(user_id)
        
        # Confirm save
        await send_message(
            message,
            f"✅ <b>Auto Leech Command Updated!</b>\n\n"
            f"New template: <code>{escape(cmd_template)}</code>\n\n"
            f"<i>The <code>{{i}}</code> placeholder will be replaced with your link/media.</i>"
        )
        
        # Delete pre-message
        if pre_message:
            await delete_message(pre_message)
            
    except Exception as e:
        LOGGER.error(f"Error setting auto leech cmd: {e}")
        await send_message(message, f"❌ Error: {str(e)}")


async def set_auto_compress_cmd(client, message, pre_message, user_id):
    """Handle auto compress command input"""
    from bot import LOGGER, database
    from bot.helper.ext_utils.db_handler import update_user_ldata
    from bot.helper.telegram_helper.message_utils import delete_message, send_message
    from html import escape
    
    try:
        compress_cmd = message.text.strip()
        
        # Update user data (allow empty to disable)
        update_user_ldata(user_id, "auto_compress_cmd", compress_cmd)
        await database.update_user_data(user_id)
        
        # Confirm save
        if compress_cmd:
            await send_message(
                message,
                f"✅ <b>Auto Compression Updated!</b>\n\n"
                f"Command: <code>{escape(compress_cmd)}</code>\n\n"
                f"<i>This will be appended to every auto leech.</i>"
            )
        else:
            await send_message(
                message,
                "✅ <b>Auto Compression Disabled</b>\n\n"
                "<i>Auto leech will work without compression.</i>"
            )
        
        # Delete pre-message
        if pre_message:
            await delete_message(pre_message)
            
    except Exception as e:
        LOGGER.error(f"Error setting auto compress cmd: {e}")
        await send_message(message, f"❌ Error: {str(e)}")
