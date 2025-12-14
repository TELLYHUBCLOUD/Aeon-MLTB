"""
Quick test script to verify compress module loads correctly
"""
import sys
import os

# Add project to path
sys.path.insert(0, r'c:\Users\Administrator\OneDrive\Desktop\DOWNLOAD\Aeon-MLTB')

print("=" * 50)
print("Testing Compress Module Imports")
print("=" * 50)

# Test 1: Import compress module
try:
    from bot.modules.compress import compress_handler, compression_callback_handler
    print("✅ compress_handler imported successfully")
    print(f"   Function: {compress_handler}")
except Exception as e:
    print(f"❌ compress_handler import FAILED: {e}")
    sys.exit(1)

# Test 2: Import state manager
try:
    from bot.helper.ext_utils.compression_state import compression_state_manager
    print("✅ compression_state_manager imported successfully")
except Exception as e:
    print(f"❌ compression_state_manager import FAILED: {e}")
    sys.exit(1)

# Test 3: Import utilities
try:
    from bot.helper.ext_utils.video_compression_utils import extract_metadata_from_partial
    print("✅ video_compression_utils imported successfully")
except Exception as e:
    print(f"❌ video_compression_utils import FAILED: {e}")
    sys.exit(1)

# Test 4: Check bot_commands
try:
    from bot.helper.telegram_helper.bot_commands import BotCommands
    print(f"✅ BotCommands.CompressCommand = '{BotCommands.CompressCommand}'")
except Exception as e:
    print(f"❌ BotCommands import FAILED: {e}")
    sys.exit(1)

# Test 5: Check if it's in modules __all__
try:
    from bot.modules import compress_handler as ch
    print(f"✅ compress_handler available from bot.modules")
except Exception as e:
    print(f"❌ compress_handler NOT in bot.modules: {e}")
    sys.exit(1)

# Test 6: Check handlers file
try:
    # Read handlers.py to verify registration
    handlers_file = r'c:\Users\Administrator\OneDrive\Desktop\DOWNLOAD\Aeon-MLTB\bot\core\handlers.py'
    with open(handlers_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'compress_handler' in content:
            print("✅ compress_handler found in handlers.py")
        else:
            print("❌ compress_handler NOT found in handlers.py")
            sys.exit(1)
except Exception as e:
    print(f"❌ Failed to read handlers.py: {e}")
    sys.exit(1)

print("=" * 50)
print("✅ ALL TESTS PASSED!")
print("=" * 50)
print("\nThe compress module is properly set up.")
print("If /compress still doesn't work, the issue is:")
print("  1. Bot not restarted after changes")
print("  2. Python cache issue (delete __pycache__ folders)")
print("  3. Bot authorization settings")
