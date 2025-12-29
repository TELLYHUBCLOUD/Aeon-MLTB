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


def music_download_cleanup():
    """
    Perform aggressive garbage collection after music downloads.
    Music downloads (Streamrip, Zotify) create many small objects for tracks,
    metadata, and temporary files that need to be cleaned up aggressively.
    """
    try:
        # Force all generations to be collected
        collected = gc.collect(2)  # Generation 2 = oldest objects
        LOGGER.info(f"Music download cleanup freed {collected} objects")
    except Exception as e:
        LOGGER.error(f"Error in music download cleanup: {e}")
