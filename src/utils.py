#!/usr/bin/env python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any


async def asyncformer(sync_func: Callable, *args, **kwargs) -> Any:
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, sync_func, *args, **kwargs)
