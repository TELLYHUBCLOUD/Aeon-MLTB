from random import randint
from aiohttp import ClientSession
from bot import LOGGER
from bot.core.config_manager import Config

# POST-based Shortener Configuration (loaded from Config)
POST_SHORTENER_CONFIG = {
    "url": Config.SHORTENER_WORKER_URL,
    "apitoken": Config.SHORTENER_API_TOKEN,
    "apiurl": Config.SHORTENER_API_URL,
    "apidomain": Config.SHORTENER_DOMAIN,
    "channels": Config.SHORTENER_CHANNELS,
    "enabled": Config.SHORTENER_ENABLED,
}


async def generate_random_password(length=4):
    """Generate random numeric password"""
    return ''.join([str(randint(0, 9)) for _ in range(length)])


async def short(long_url, alias=None, expiry=7, password="auto"):
    if not POST_SHORTENER_CONFIG.get("enabled"):
        LOGGER.warning("POST shortener is disabled")
        return long_url
    
    if not POST_SHORTENER_CONFIG.get("apitoken"):
        LOGGER.warning("POST shortener API token not configured")
        return long_url
    
    # Generate random password if "auto"
    if password == "auto":
        password = await generate_random_password()
    
    try:
        payload = {
            "url": long_url,
            "expiry": expiry,
            "apitoken": POST_SHORTENER_CONFIG["apitoken"],
            "apiurl": POST_SHORTENER_CONFIG["apiurl"],
            "apidomain": POST_SHORTENER_CONFIG["apidomain"],
            "channels": POST_SHORTENER_CONFIG["channels"],
        }
        
        # Add optional fields
        if alias:
            payload["alias"] = alias
        if password:
            payload["password"] = password
        
        async with ClientSession() as session:
            async with session.post(
                POST_SHORTENER_CONFIG["url"],
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        short_url = result.get("shortUrl")
                        LOGGER.info(f"Shortened: {long_url} -> {short_url}")
                        if password:
                            LOGGER.info(f"Password: {password}")
                        return short_url
                else:
                    error_text = await response.text()
                    LOGGER.error(f"Shortener failed: {response.status} - {error_text}")
    except Exception as e:
        LOGGER.error(f"Shortener error: {e}")
    
    # Return original URL if failed
    return long_url
