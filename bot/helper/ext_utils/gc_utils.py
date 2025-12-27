#!/usr/bin/env python3
import gc
from logging import getLogger

LOGGER = getLogger(__name__)

async def smart_garbage_collection():
    """
    Perform manual garbage collection to free up memory.
    Useful for Heroku dynos with tight memory quotas.
    """
    try:
        before = gc.collect()
        LOGGER.info(f"Garbage collection freed {before} objects")
    except Exception as e:
        LOGGER.error(f"Error in garbage collection: {e}")
