from asyncio import sleep
from random import choice
from urllib.parse import quote
from aiohttp import ClientSession
from pyshorteners import Shortener
from bot import shorteners_list

# Cloudflare Worker URL (Apna worker URL yahan daalein)
WORKER_URL = "https://tellylinks.tellycloudapi.workers.dev/shorten"

async def short(long_url):
    """
    Shortens URL with multiple fallback methods:
    1. Cloudflare Worker (GPLinks) - Primary
    2. Custom shorteners list - Secondary
    3. TinyURL - Final fallback
    
    Args:
        long_url: The long URL to be shortened.
    
    Returns:
        Shortened URL (worker domain preferred) or original URL if all fail.
    """
    
    async with ClientSession() as session:
        
        # Method 1: Try Cloudflare Worker first (GPLinks with worker domain)
        try:
            async with session.get(
                f"{WORKER_URL}?url={quote(long_url)}",
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        # Worker domain URL milega: https://your-worker.workers.dev/hh5CY9
                        return result.get("shortUrl")
        except Exception as e:
            print(f"Worker failed: {e}")
        
        # Method 2: Try custom shorteners list (fallback)
        if shorteners_list:
            for _attempt in range(3):
                shortener_info = choice(shorteners_list)
                try:
                    async with session.get(
                        f"https://{shortener_info['domain']}/api?api={shortener_info['api_key']}&url={quote(long_url)}",
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            short_url = result.get("shortenedUrl", long_url)
                            if short_url != long_url:
                                return short_url
                except Exception as e:
                    print(f"Custom shortener failed: {e}")
                    continue
        
        # Method 3: Final fallback to TinyURL
        s = Shortener()
        for _attempt in range(3):
            try:
                return s.tinyurl.short(long_url)
            except Exception as e:
                print(f"TinyURL attempt {_attempt + 1} failed: {e}")
                await sleep(1)
        
        # If all methods fail, return original URL
        return long_url
